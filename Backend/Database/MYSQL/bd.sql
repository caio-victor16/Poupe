drop database if exists poupe;
create database poupe;
use poupe;

create table usuario (
    id_usuario int auto_increment primary key,
    nome varchar(100) not null,
    email varchar(150) not null unique,
    telefone varchar(20),
    senha varchar(255) not null,
    renda_mensal decimal(10,2) not null,
    limite_gastos decimal(10,2) not null
);

create table categoria (
    id_categoria int auto_increment primary key,
    nome varchar(60) not null
);

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