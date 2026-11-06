# Correção 4 — consumo da IA e privacidade dos logs

1. A rota /ia continua exigindo login. A identidade vem da sessão, nunca de
   um ID informado no JSON. Mensagens vazias ou com mais de 2000 caracteres
   são rejeitadas antes de consumir a cota.
2. Antes de chamar o Gemini, o servidor reserva uma chamada nos contadores
   do usuário e globais, numa transação atômica. Chamadas concorrentes não
   podem ultrapassar o teto. Falhas do provedor também consomem essa reserva:
   um timeout não garante que o provedor deixou de processar a chamada.
3. Os valores padrão são 5 por minuto e 50 por dia por usuário; 30 por minuto
   e 500 por dia para todo o aplicativo. Altere no .env, se necessário:

```dotenv
IA_LIMITE_MINUTO=5
IA_LIMITE_DIA=50
IA_LIMITE_GLOBAL_MINUTO=30
IA_LIMITE_GLOBAL_DIA=500
```

Use inteiros não negativos. Zero bloqueia chamadas. Reinicie o servidor após
alterar a configuração. As janelas são fixas: minutos do relógio e dias UTC,
não intervalos móveis. Pode haver chamadas próximas nos dois lados da virada.

4. Ao atingir o limite, a API responde 429, com Retry-After e uma mensagem
   legível. O frontend já mostra a mensagem de erro recebida. Quando o contador
   está indisponível, a API responde 503 e não chama o provedor.
5. O arquivo instance/ia_limites.sqlite3 é criado automaticamente. Ele contém
   apenas contadores e identificadores, nunca mensagens. Preserve-o entre
   reinicializações; não o envie ao Git. Os processos locais compartilham esse
   arquivo. Em implantação com vários servidores, substitua por um contador
   central compartilhado; arquivos locais separados não impõem um teto único.
6. Cada mensagem dispara no máximo uma chamada ao modelo configurado.
   Foram removidos fallback e repetições automáticas, incluindo após timeout.
   Se o modelo não estiver disponível, o usuário recebe erro; configure
   GEMINI_MODEL para outro modelo válido quando necessário.
7. Prompts, respostas, chave e exceções brutas não são mais impressos. Os logs
   novos contêm somente avisos genéricos de falha. Logs antigos não são apagados
   por esta correção e podem conter conversas registradas anteriormente.

Testes: `python -m unittest discover -s tests -v`. As chamadas ao Gemini são
simuladas, sem custos. Cobrem concorrência, isolamento de cotas, virada da
janela, logout, indisponibilidade do contador e ausência de prints privados.

O limite é de quantidade de chamadas, não de valor monetário. O custo também
depende do modelo e da resposta. O teto global limita o consumo mesmo com
várias contas, mas não substitui limites de orçamento no provedor.
