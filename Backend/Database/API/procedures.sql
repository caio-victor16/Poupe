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