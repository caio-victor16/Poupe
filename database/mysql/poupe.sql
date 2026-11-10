-- =============================================================
-- Banco de dados: poupe
-- Referenciado em backend/config.py (MYSQL_DATABASE = "poupe")
-- Schema batendo com os models em backend/models/*.py
--
-- Este script NÃO apaga bancos. O setup_db.py ignora as duas linhas
-- abaixo e usa o nome definido em MYSQL_DATABASE. Para recriar do zero:
--   python setup_db.py --reset --confirmar <nome_do_banco>
-- Execução manual (Workbench): ajuste o nome abaixo se usar outro banco.
-- =============================================================

create database if not exists poupe;
use poupe;

-- ---------------------------------------------------------------
-- usuario  -> backend/models/usuario.py
-- ---------------------------------------------------------------
create table usuario (
    id_usuario int auto_increment primary key,
    nome varchar(100) not null,
    email varchar(150) not null unique,
    telefone varchar(20),
    senha varchar(255) not null,
    renda_mensal decimal(10,2) not null,
    limite_gastos decimal(10,2) not null,
    -- Evidência do consentimento (LGPD, art. 8º): quando e qual versão do termo foi aceita.
    termos_aceitos_em datetime null,
    termos_versao varchar(20) null
);

-- ---------------------------------------------------------------
-- sessao_usuario -> backend/models/seguranca.py (REV-002)
-- Uma linha por login. O cookie guarda o token; aqui fica só o hash.
-- Logout e troca de senha apagam a linha, invalidando o cookie.
-- ---------------------------------------------------------------
create table sessao_usuario (
    token_hash char(64) primary key,
    id_usuario int not null,
    expira_em datetime not null,

    index idx_sessao_usuario (id_usuario),

    foreign key (id_usuario)
        references usuario(id_usuario)
        on delete cascade
);

-- ---------------------------------------------------------------
-- redefinicao_senha -> backend/models/seguranca.py ("esqueci a senha")
-- Link enviado por e-mail: vale 30 min e uma vez. Aqui fica só o hash.
-- ---------------------------------------------------------------
create table redefinicao_senha (
    token_hash char(64) primary key,
    id_usuario int not null,
    expira_em datetime not null,

    index idx_redefinicao_usuario (id_usuario),

    foreign key (id_usuario)
        references usuario(id_usuario)
        on delete cascade
);

-- ---------------------------------------------------------------
-- tentativa_acesso -> backend/models/seguranca.py (REV-001)
-- Falhas de login e cadastros recentes, para limitar força bruta.
-- ---------------------------------------------------------------
create table tentativa_acesso (
    id_tentativa int auto_increment primary key,
    chave varchar(190) not null,
    momento datetime not null,

    index idx_tentativa_chave_momento (chave, momento),
    index idx_tentativa_momento (momento)
);

-- ---------------------------------------------------------------
-- categoria -> backend/models/categoria.py
-- ---------------------------------------------------------------
create table categoria (
    id_categoria int auto_increment primary key,
    nome varchar(60) not null
);

-- ---------------------------------------------------------------
-- gasto -> backend/models/gasto.py
-- ---------------------------------------------------------------
create table gasto (
    id_gasto int auto_increment primary key,

    id_usuario int not null,
    id_categoria int not null,

    valor decimal(10,2) not null,
    data date not null,
    descricao varchar(255),
    recorrente boolean default false,
    tipo_pagamento varchar(50),
    status_gasto varchar(30),

    foreign key (id_usuario)
        references usuario(id_usuario)
        on delete cascade,

    foreign key (id_categoria)
        references categoria(id_categoria)
);

-- ---------------------------------------------------------------
-- boleto -> backend/models/boleto.py
-- ---------------------------------------------------------------
-- Aba Boletos: contas a pagar. "fixo" repete todo mês (ao pagar, cria o do
-- mês seguinte); "debito_automatico" lança o pagamento sozinho no vencimento.
-- Pagar cria o gasto (id_gasto). Código de barras é opcional.
create table boleto (
    id_boleto int auto_increment primary key,

    id_usuario int not null,

    descricao varchar(100) not null default '',
    id_categoria int null,
    codigo_barras varchar(100) null,
    valor decimal(10,2) not null,
    vencimento date not null,
    status varchar(30),
    fixo boolean not null default false,
    debito_automatico boolean not null default false,
    dia_vencimento int null,
    data_pagamento date null,
    id_gasto int null,

    foreign key (id_usuario)
        references usuario(id_usuario)
        on delete cascade,

    constraint fk_boleto_categoria foreign key (id_categoria)
        references categoria(id_categoria),

    constraint fk_boleto_gasto foreign key (id_gasto)
        references gasto(id_gasto)
        on delete set null
);

-- ---------------------------------------------------------------
-- alerta -> backend/models/alerta.py
-- ---------------------------------------------------------------
create table alerta (
    id_alerta int auto_increment primary key,

    id_usuario int not null,

    tipo varchar(60),
    mensagem text,
    data datetime default current_timestamp,
    visualizado boolean default false,

    foreign key (id_usuario)
        references usuario(id_usuario)
        on delete cascade
);

-- ---------------------------------------------------------------
-- previsao_financeira -> não tem model SQLAlchemy (backend/models/previsao.py
-- é só um DTO em memória), mas é usada pela procedure
-- sp_previsao_financeira chamada em previsao_repository.py
-- ---------------------------------------------------------------
create table previsao_financeira (
    id_previsao int auto_increment primary key,

    id_usuario int not null,

    valor_previsto decimal(10,2),
    data_previsao date,
    risco_endividamento varchar(30),
    recomendacao text,

    foreign key (id_usuario)
        references usuario(id_usuario)
        on delete cascade
);

-- ---------------------------------------------------------------
-- extrato -> ainda sem controller/service/repository no código;
-- mantida por já fazer parte do schema original
-- ---------------------------------------------------------------
create table extrato (
    id_extrato int auto_increment primary key,

    id_usuario int not null,

    banco varchar(80),
    nome_arquivo varchar(255),
    data_importacao datetime default current_timestamp,

    foreign key (id_usuario)
        references usuario(id_usuario)
        on delete cascade
);

-- ---------------------------------------------------------------
-- orcamento_categoria -> limite mensal por categoria (orcamento.html)
-- ---------------------------------------------------------------
create table orcamento_categoria (
    id_orcamento int auto_increment primary key,

    id_usuario int not null,
    id_categoria int not null,

    limite decimal(10,2) not null,

    foreign key (id_usuario)
        references usuario(id_usuario)
        on delete cascade,

    foreign key (id_categoria)
        references categoria(id_categoria)
);

-- ---------------------------------------------------------------
-- receita -> receitas do usuário (receitas.html)
-- ---------------------------------------------------------------
create table receita (
    id_receita int auto_increment primary key,

    id_usuario int not null,

    descricao varchar(255) not null,
    categoria varchar(60) not null,
    valor decimal(10,2) not null,
    data date not null,

    index idx_receita_usuario_data (id_usuario, data),

    foreign key (id_usuario)
        references usuario(id_usuario)
        on delete cascade
);

-- ---------------------------------------------------------------
-- receita_recorrente -> receitas fixas mensais (recorrencia.html)
-- ---------------------------------------------------------------
create table receita_recorrente (
    id_receita_recorrente int auto_increment primary key,

    id_usuario int not null,

    descricao varchar(255) not null,
    categoria varchar(60) not null,
    valor decimal(10,2) not null,
    dia_mes int not null,
    proxima_data date not null,
    ativa boolean not null default true,

    index idx_receita_recorrente_usuario_data (id_usuario, proxima_data),

    foreign key (id_usuario)
        references usuario(id_usuario)
        on delete cascade
);

-- ---------------------------------------------------------------
-- conta -> contas e saldos do caixa (caixa.html)
-- ---------------------------------------------------------------
create table conta (
    id_conta int auto_increment primary key,

    id_usuario int not null,

    nome varchar(100) not null,
    tipo varchar(30) not null,
    saldo decimal(10,2) not null,

    foreign key (id_usuario)
        references usuario(id_usuario)
        on delete cascade
);

-- ---------------------------------------------------------------
-- meta -> metas de economia (metas.html)
-- ---------------------------------------------------------------
create table meta (
    id_meta int auto_increment primary key,

    id_usuario int not null,

    titulo varchar(100) not null,
    valor_alvo decimal(10,2) not null,
    valor_guardado decimal(10,2) not null default 0,

    foreign key (id_usuario)
        references usuario(id_usuario)
        on delete cascade
);

-- ---------------------------------------------------------------
-- cofrinho -> cofrinhos com prazo e aportes (cofrinho.html)
-- ---------------------------------------------------------------
create table cofrinho (
    id_cofrinho int auto_increment primary key,

    id_usuario int not null,

    titulo varchar(100) not null,
    valor_alvo decimal(10,2) not null,
    valor_guardado decimal(10,2) not null default 0,
    prazo_meses int not null,

    foreign key (id_usuario)
        references usuario(id_usuario)
        on delete cascade
);

-- ---------------------------------------------------------------
-- recorrencia_gasto -> gastos fixos/recorrentes (recorrencia.html)
-- ---------------------------------------------------------------
create table recorrencia_gasto (
    id_recorrencia int auto_increment primary key,

    id_usuario int not null,
    id_categoria int not null,

    valor decimal(10,2) not null,
    descricao varchar(255),
    frequencia varchar(20) not null,
    proxima_data date not null,
    dia_mes int not null,
    tipo_pagamento varchar(50),
    ativa boolean not null default true,

    foreign key (id_usuario)
        references usuario(id_usuario)
        on delete cascade,

    foreign key (id_categoria)
        references categoria(id_categoria)
);

-- ---------------------------------------------------------------
-- seed de categorias padrão
-- ---------------------------------------------------------------
insert into categoria (nome)
values
('alimentação'),
('transporte'),
('saúde'),
('lazer'),
('moradia'),
('educação'),
('compras'),
('energia'),
('internet'),
('outros');


-- =============================================================
-- Stored procedures usadas pelos repositories (via db.session.execute(text(...)))
-- =============================================================

delimiter $$

-- usada em: relatorio_repository / relatorio_service (relatório por categoria)
create procedure sp_gastos_categoria(
    in p_usuario int
)
begin

    select
        c.nome as categoria,
        sum(g.valor) as total_gasto
    from
        gasto g
        inner join categoria c on g.id_categoria = c.id_categoria
    where
        g.id_usuario = p_usuario
    group by
        c.nome
    order by
        total_gasto desc;

end $$

-- usada em: gasto_repository (listagem filtrada por período)
create procedure sp_gastos_por_periodo(
    in p_id_usuario int,
    in p_data_inicio date,
    in p_data_fim date
)
begin

    select
        g.id_gasto,
        g.valor,
        g.data,
        g.descricao,
        g.recorrente,
        g.tipo_pagamento,
        g.status_gasto,
        c.nome as categoria

    from gasto g

    inner join categoria c
        on g.id_categoria = c.id_categoria

    where g.id_usuario = p_id_usuario
      and g.data between p_data_inicio and p_data_fim

    order by g.data desc;

end $$

-- usada em: gasto_repository (checagem de limite)
-- Considera só os gastos do mês atual (mesmo critério do score).
create procedure sp_verificar_limite_gastos(
    in p_id_usuario int
)
begin

    select
        u.id_usuario,
        u.nome,
        u.renda_mensal,
        u.limite_gastos,
        coalesce(sum(g.valor), 0) as total_gasto,

        round(
            (
                coalesce(sum(g.valor), 0)
                / nullif(u.limite_gastos, 0)
            ) * 100,
            2
        ) as percentual_utilizado,

        case
            when coalesce(sum(g.valor), 0) >= u.limite_gastos
                then 'limite_excedido'
            when coalesce(sum(g.valor), 0) >= u.limite_gastos * 0.8
                then 'proximo_do_limite'
            else 'dentro_do_limite'
        end as situacao

    from usuario u

    left join gasto g
        on g.id_usuario = u.id_usuario
       and g.data >= date_format(curdate(), '%Y-%m-01')
       and g.data <  date_add(date_format(curdate(), '%Y-%m-01'), interval 1 month)

    where u.id_usuario = p_id_usuario

    group by
        u.id_usuario,
        u.nome,
        u.renda_mensal,
        u.limite_gastos;

end $$

-- usada em: boleto_repository (boletos vencendo em até 7 dias)
create procedure sp_boletos_proximos_vencimento(
    in p_id_usuario int
)
begin

    select
        id_boleto,
        id_usuario,
        codigo_barras,
        valor,
        vencimento,
        status,
        datediff(vencimento, curdate()) as dias_para_vencimento

    from boleto

    where id_usuario = p_id_usuario
      and status <> 'pago'
      and vencimento >= curdate()
      and vencimento <= date_add(curdate(), interval 7 day)

    order by vencimento asc;

end $$

-- usada em: alerta_service (gera alerta automático de limite)
-- Considera só os gastos do mês atual. Cria no máximo UM alerta de cada
-- situação ("próximo" e "ultrapassado") por usuário e por mês (item 14):
-- chamadas repetidas, a cada gasto cadastrado, não duplicam o alerta.
create procedure sp_gerar_alerta_limite(
    in p_id_usuario int
)
begin

    declare v_limite decimal(10,2);
    declare v_total decimal(10,2);
    declare v_percentual decimal(10,2);
    declare v_mensagem varchar(255) default null;
    declare v_inicio_mes date default date_format(curdate(), '%Y-%m-01');
    declare v_trava varchar(64) default concat('poupe_alerta_limite_', p_id_usuario);

    select limite_gastos
    into v_limite
    from usuario
    where id_usuario = p_id_usuario;

    select coalesce(sum(valor), 0)
    into v_total
    from gasto
    where id_usuario = p_id_usuario
      and data >= v_inicio_mes
      and data <  date_add(v_inicio_mes, interval 1 month);

    if v_limite > 0 then

        set v_percentual = (v_total / v_limite) * 100;

        if v_percentual >= 100 then
            set v_mensagem = 'seu limite de gastos foi ultrapassado.';
        elseif v_percentual >= 80 then
            set v_mensagem = 'você está próximo do seu limite de gastos.';
        end if;

    end if;

    if v_mensagem is not null then

        -- Trava por usuário: duas chamadas ao mesmo tempo não criam dois alertas.
        if get_lock(v_trava, 5) = 1 then

            insert into alerta
                (id_usuario, tipo, mensagem, data, visualizado)
            select p_id_usuario, 'limite', v_mensagem, now(), false
            from dual
            where not exists (
                select 1
                from alerta
                where id_usuario = p_id_usuario
                  and tipo = 'limite'
                  and mensagem = v_mensagem
                  and data >= v_inicio_mes
                  and data <  date_add(v_inicio_mes, interval 1 month)
            );

            do release_lock(v_trava);

        end if;

    end if;

end $$

-- usada em: relatorio_repository / relatorio_service (relatório financeiro geral)
create procedure sp_relatorio_financeiro(
    in p_id_usuario int
)
begin

    select
        u.id_usuario,
        u.nome,
        u.renda_mensal,
        u.limite_gastos,

        (
            select coalesce(sum(g.valor), 0)
            from gasto g
            where g.id_usuario = u.id_usuario
        ) as total_gastos,

        (
            select count(*)
            from gasto g
            where g.id_usuario = u.id_usuario
        ) as quantidade_gastos,

        (
            select coalesce(sum(b.valor), 0)
            from boleto b
            where b.id_usuario = u.id_usuario
              and b.status <> 'pago'
        ) as total_boletos_pendentes,

        (
            select count(*)
            from boleto b
            where b.id_usuario = u.id_usuario
              and b.status <> 'pago'
        ) as quantidade_boletos_pendentes,

        round(
            (
                (
                    select coalesce(sum(g.valor), 0)
                    from gasto g
                    where g.id_usuario = u.id_usuario
                )
                / u.limite_gastos
            ) * 100,
            2
        ) as percentual_limite_utilizado

    from usuario u

    where u.id_usuario = p_id_usuario;

end $$

-- usada em: previsao_repository (chamada via CALL sp_previsao_financeira(:id_usuario))
create procedure sp_previsao_financeira(
    in p_id_usuario int
)
begin

    declare v_renda decimal(10,2);
    declare v_limite decimal(10,2);
    declare v_gasto_atual decimal(10,2);
    declare v_dias_passados int;
    declare v_dias_mes int;
    declare v_media_diaria decimal(10,2);
    declare v_previsao decimal(10,2);

    select renda_mensal, limite_gastos
    into v_renda, v_limite
    from usuario
    where id_usuario = p_id_usuario;

    select coalesce(sum(valor), 0)
    into v_gasto_atual
    from gasto
    where id_usuario = p_id_usuario
      and month(data) = month(curdate())
      and year(data) = year(curdate());

    set v_dias_passados = day(curdate());
    set v_dias_mes = day(last_day(curdate()));

    if v_dias_passados > 0 then
        set v_media_diaria = v_gasto_atual / v_dias_passados;
    else
        set v_media_diaria = 0;
    end if;

    set v_previsao = v_media_diaria * v_dias_mes;

    select
        p_id_usuario as id_usuario,
        v_renda as renda_mensal,
        v_limite as limite_gastos,
        v_gasto_atual as gasto_atual,
        v_media_diaria as media_diaria,
        v_previsao as previsao_fim_mes,

        case
            when v_previsao > v_limite
                then 'acima_do_limite'
            when v_previsao >= v_limite * 0.8
                then 'proximo_do_limite'
            else 'dentro_do_limite'
        end as situacao;

end $$

-- usada em: caixa_repository (média de gastos e boletos pendentes em 30 dias)
create procedure sp_caixa_calcular(
    in p_id_usuario int
)
begin

    select
        (
            select coalesce(sum(g.valor), 0) / 30
            from gasto g
            where g.id_usuario = u.id_usuario
              and g.data >= date_sub(curdate(), interval 30 day)
              and g.data <= curdate()
        ) as media_diaria,
        (
            select coalesce(sum(b.valor), 0)
            from boleto b
            where b.id_usuario = u.id_usuario
              and coalesce(b.status, '') <> 'pago'
              and b.vencimento <= date_add(curdate(), interval 30 day)
        ) as boletos_30_dias
    from usuario u
    where u.id_usuario = p_id_usuario;

end $$

-- usada em: cofrinho_repository (simulação de troco arredondado)
create procedure sp_cofrinho_simular(
    in p_id_usuario int,
    in p_passo decimal(10,2),
    in p_dias int
)
begin

    select
        coalesce(sum(ceil(valor / p_passo) * p_passo - valor), 0) as troco,
        count(*) as quantidade
    from gasto
    where id_usuario = p_id_usuario
      and data >= date_sub(curdate(), interval p_dias day)
      and data <= curdate();

end $$

-- usada em: desperdicio_repository (categorias com gasto atual acima da média)
create procedure sp_desperdicio_categorias_acima_media(
    in p_id_usuario int
)
begin

    select
        categoria,
        mes_atual,
        round(media, 2) as media_mensal,
        round(mes_atual - media, 2) as excesso
    from (
        select
            c.nome as categoria,
            coalesce(sum(case when g.data >= date_format(curdate(), '%Y-%m-01')
                              then g.valor end), 0) as mes_atual,
            coalesce(sum(case when g.data < date_format(curdate(), '%Y-%m-01')
                              then g.valor end), 0)
            / nullif(count(distinct case when g.data < date_format(curdate(), '%Y-%m-01')
                                         then date_format(g.data, '%Y-%m') end), 0) as media
        from gasto g
        inner join categoria c on c.id_categoria = g.id_categoria
        where g.id_usuario = p_id_usuario
          and g.data >= date_sub(date_format(curdate(), '%Y-%m-01'), interval 3 month)
        group by c.nome
    ) t
    where media >= 30
      and mes_atual > media
    order by excesso desc;

end $$

-- usada em: desperdicio_repository (gastos recorrentes com valor estável)
create procedure sp_desperdicio_assinaturas_provaveis(
    in p_id_usuario int
)
begin

    select
        lower(trim(descricao)) as descricao,
        count(distinct date_format(data, '%Y-%m')) as meses,
        round(avg(valor), 2) as valor_mensal,
        round(avg(valor) * 12, 2) as custo_anual
    from gasto
    where id_usuario = p_id_usuario
      and trim(coalesce(descricao, '')) <> ''
      and data >= date_sub(curdate(), interval 4 month)
    group by lower(trim(descricao))
    having count(distinct date_format(data, '%Y-%m')) >= 2
       and count(*) <= count(distinct date_format(data, '%Y-%m'))
       and (max(valor) - min(valor)) <= avg(valor) * 0.1
    order by avg(valor) desc;

end $$

-- usada em: desperdicio_repository (possíveis lançamentos repetidos)
create procedure sp_desperdicio_gastos_duplicados(
    in p_id_usuario int
)
begin

    select
        descricao,
        valor,
        data,
        count(*) as vezes
    from gasto
    where id_usuario = p_id_usuario
      and data >= date_sub(curdate(), interval 30 day)
    group by descricao, valor, data
    having count(*) > 1
    order by data desc;

end $$

-- usada em: orcamento_repository (limite e gasto do mês por categoria)
create procedure sp_orcamento_status_mes(
    in p_id_usuario int
)
begin

    select
        o.id_orcamento,
        o.id_categoria,
        c.nome as categoria,
        o.limite,
        coalesce(sum(g.valor), 0) as gasto_mes
    from orcamento_categoria o
    inner join categoria c on c.id_categoria = o.id_categoria
    left join gasto g
        on g.id_usuario = o.id_usuario
       and g.id_categoria = o.id_categoria
       and g.data >= date_format(curdate(), '%Y-%m-01')
       and g.data < date_add(date_format(curdate(), '%Y-%m-01'), interval 1 month)
    where o.id_usuario = p_id_usuario
    group by o.id_orcamento, o.id_categoria, c.nome, o.limite
    order by c.nome;

end $$

-- usada em: score_repository (indicadores que compõem o score financeiro)
create procedure sp_score_indicadores(
    in p_id_usuario int
)
begin

    select
        u.renda_mensal,
        u.limite_gastos,
        (
            select coalesce(sum(g.valor), 0)
            from gasto g
            where g.id_usuario = u.id_usuario
              and g.data >= date_format(curdate(), '%Y-%m-01')
              and g.data < date_add(date_format(curdate(), '%Y-%m-01'), interval 1 month)
        ) as gasto_mes,
        (
            select count(*)
            from boleto b
            where b.id_usuario = u.id_usuario
              and b.status <> 'pago'
              and b.vencimento < curdate()
        ) as boletos_atrasados,
        (
            select count(*)
            from boleto b
            where b.id_usuario = u.id_usuario
              and b.status <> 'pago'
              and b.vencimento between curdate() and date_add(curdate(), interval 7 day)
        ) as boletos_na_semana
    from usuario u
    where u.id_usuario = p_id_usuario;

end $$

delimiter ;
