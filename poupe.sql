-- =============================================================
-- Banco de dados: poupe
-- Referenciado em backend/config.py (MYSQL_DATABASE = "poupe")
-- Schema batendo com os models em backend/models/*.py
-- =============================================================

drop database if exists poupe;
create database poupe;
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
    limite_gastos decimal(10,2) not null
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
create table boleto (
    id_boleto int auto_increment primary key,

    id_usuario int not null,

    codigo_barras varchar(100) not null,
    valor decimal(10,2) not null,
    vencimento date not null,
    status varchar(30),

    foreign key (id_usuario)
        references usuario(id_usuario)
        on delete cascade
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

-- usada em: alerta_repository / alerta_service (checagem de limite)
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
                / u.limite_gastos
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
create procedure sp_gerar_alerta_limite(
    in p_id_usuario int
)
begin

    declare v_limite decimal(10,2);
    declare v_total decimal(10,2);
    declare v_percentual decimal(10,2);

    select limite_gastos
    into v_limite
    from usuario
    where id_usuario = p_id_usuario;

    select coalesce(sum(valor), 0)
    into v_total
    from gasto
    where id_usuario = p_id_usuario;

    if v_limite > 0 then

        set v_percentual = (v_total / v_limite) * 100;

        if v_percentual >= 100 then

            insert into alerta
                (id_usuario, tipo, mensagem, data, visualizado)
            values
                (p_id_usuario, 'limite', 'seu limite de gastos foi ultrapassado.', now(), false);

        elseif v_percentual >= 80 then

            insert into alerta
                (id_usuario, tipo, mensagem, data, visualizado)
            values
                (p_id_usuario, 'limite', 'você está próximo do seu limite de gastos.', now(), false);

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

delimiter ;
