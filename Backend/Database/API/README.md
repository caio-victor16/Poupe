# POUPE+

Sistema de gerenciamento financeiro desenvolvido com Flask, MySQL e arquitetura em camadas.

O POUPE+ tem como objetivo auxiliar o usuário no controle de gastos, boletos e organização financeira, oferecendo consultas e análises além das operações básicas de cadastro.

## Tecnologias utilizadas

- Python
- Flask
- MySQL
- MySQL Connector
- Thunder Client para testes da API

## Arquitetura

O projeto utiliza uma arquitetura dividida em camadas:

```text
Controller
    ↓
Service
    ↓
Repository
    ↓
Procedure
    ↓
MySQL