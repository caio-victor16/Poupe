delimiter $

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
    
end $
delimiter ;


delimiter $$

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

delimiter ;

delimiter $$

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

delimiter ;


delimiter $$

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

      and vencimento <= date_add(
          curdate(),
          interval 7 day
      )

    order by vencimento asc;

end $$

delimiter ;

delimiter $$

create procedure sp_gerar_alerta_limite(
    in p_id_usuario int
)
begin

    declare v_limite decimal(10,2);
    declare v_total decimal(10,2);
    declare v_percentual decimal(10,2);

    select
        limite_gastos
    into v_limite
    from usuario
    where id_usuario = p_id_usuario;

    select
        coalesce(sum(valor), 0)
    into v_total
    from gasto
    where id_usuario = p_id_usuario;

    if v_limite > 0 then

        set v_percentual =
            (v_total / v_limite) * 100;

        if v_percentual >= 100 then

            insert into alerta
            (
                id_usuario,
                tipo,
                mensagem,
                data,
                visualizado
            )
            values
            (
                p_id_usuario,
                'limite',
                'seu limite de gastos foi ultrapassado.',
                now(),
                false
            );

        elseif v_percentual >= 80 then

            insert into alerta
            (
                id_usuario,
                tipo,
                mensagem,
                data,
                visualizado
            )
            values
            (
                p_id_usuario,
                'limite',
                'você está próximo do seu limite de gastos.',
                now(),
                false
            );

        end if;

    end if;

end $$

delimiter ;

delimiter $$

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

delimiter ;

delimiter $$

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

    select
        renda_mensal,
        limite_gastos
    into
        v_renda,
        v_limite
    from usuario
    where id_usuario = p_id_usuario;

    select
        coalesce(sum(valor), 0)
    into
        v_gasto_atual
    from gasto
    where id_usuario = p_id_usuario
      and month(data) = month(curdate())
      and year(data) = year(curdate());

    set v_dias_passados = day(curdate());

    set v_dias_mes = day(
        last_day(curdate())
    );

    if v_dias_passados > 0 then

        set v_media_diaria =
            v_gasto_atual / v_dias_passados;

    else

        set v_media_diaria = 0;

    end if;

    set v_previsao =
        v_media_diaria * v_dias_mes;

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