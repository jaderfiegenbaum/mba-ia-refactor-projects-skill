# Template do Relatório de Auditoria

A saída da Fase 2 deve seguir exatamente esta estrutura. Preencha todos os campos, sem deixar placeholder no relatório final.

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: <nome da pasta do projeto>
Stack:   <linguagem + framework>
Files:   <N> analyzed | ~<N> lines of code

## Summary
CRITICAL: <N> | HIGH: <N> | MEDIUM: <N> | LOW: <N>

## Findings

### [<SEVERIDADE>] <Nome curto do anti pattern>
File: <arquivo>:<linha ou intervalo de linhas>
Description: <o que foi encontrado, específico ao trecho de código>
Impact: <consequência concreta se isso não for corrigido>
Recommendation: <o que fazer para corrigir, referenciando o padrão de transformação usado>

### [<SEVERIDADE>] <Nome curto do anti pattern>
File: <arquivo>:<linha ou intervalo de linhas>
Description: ...
Impact: ...
Recommendation: ...

(um bloco ### por finding, repetido para todos os findings)

================================
Total: <N> findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```

## Regras de preenchimento

- **Ordem dos findings**: sempre do mais severo para o menos severo, CRITICAL primeiro, LOW por último. Dentro da mesma severidade, ordene pela ordem em que o arquivo aparece no projeto.
- **File**: sempre o caminho relativo do arquivo a partir da raiz do projeto, seguido de `:` e o número da linha ou o intervalo exato (`models.py:28` ou `models.py:171-201`). Nunca aproxime ("por volta da linha 100"), releia o arquivo para confirmar o número exato antes de reportar.
- **Description**: descreva o que o código faz hoje, de forma específica ao trecho encontrado, não uma definição genérica do anti pattern. Cite nomes de função, variável ou rota reais quando ajudar a identificar o trecho.
- **Impact**: uma frase concreta sobre a consequência prática, não abstrata. Prefira "qualquer usuário autenticado pode ler o pedido de outro usuário trocando o id na URL" a "problema de segurança".
- **Recommendation**: aponte a direção da correção, alinhada ao padrão correspondente em `references/refactoring-playbook.md`, mas sem repetir o playbook inteiro aqui. Uma ou duas frases bastam.
- **Summary**: a soma dos contadores por severidade deve bater exatamente com o "Total" ao final e com o número de blocos `###` no relatório.
- **Lines of code**: uma contagem aproximada, mas plausível, das linhas de código fonte da aplicação (pode usar `wc -l` sobre os arquivos analisados, excluindo dependências).

Depois de imprimir o relatório completo, pare e aguarde a resposta do usuário à pergunta final antes de iniciar a Fase 3. Não prossiga com nenhuma modificação de arquivo enquanto essa confirmação não for dada explicitamente.
