# Como rodar o FatOutFitIn

## Caminho mais fácil: dois cliques no Windows

### 1. Instale os dois pré-requisitos, uma única vez

- **Python 3.10 ou superior:** baixe no [site oficial do Python para Windows](https://www.python.org/downloads/windows/). Se o instalador mostrar a opção **Add python.exe to PATH**, marque-a.
- **Java JDK 17 ou superior:** baixe o [Eclipse Temurin JDK 17 para Windows](https://adoptium.net/temurin/releases/?version=17&os=windows&arch=x64). Escolha **JDK**, Windows e o instalador adequado ao computador. Se disponíveis no instalador, habilite a inclusão no PATH e a configuração de JAVA_HOME.

Depois de instalar, feche e reabra a janela de terminal que já estava aberta. Neste computador, Python e JDK já estavam disponíveis durante os testes.

Não é necessário instalar Maven separadamente, Node.js, Docker ou um servidor de banco de dados.

### 2. Extraia o projeto

1. Baixe o ZIP atualizado do projeto.
2. Clique com o botão direito no ZIP e escolha **Extrair Tudo**.
3. Abra a pasta extraída **FatOutFitIn**, que contém `INICIAR.cmd`, `iniciar.py`, `api-python`, `api-java` e `frontend`.

Execute os arquivos da pasta extraída. Não abra o programa de dentro do ZIP.

### 3. Abra INICIAR.cmd

Dê **dois cliques em `INICIAR.cmd`**. Se o Explorador ocultar extensões, ele pode aparecer como **INICIAR**, do tipo “Script de Comandos do Windows”.

Uma única janela vai:

1. Criar o ambiente Python e instalar suas dependências.
2. Baixar o Maven e as bibliotecas Java, e compilar o projeto quando necessário.
3. Iniciar as duas APIs em portas livres.
4. Servir a página e abrir o navegador quando tudo estiver pronto.

**Na primeira vez, mantenha a internet conectada e aguarde.** O download e a compilação podem levar alguns minutos. As próximas execuções reaproveitam os arquivos já preparados e normalmente iniciam mais rápido.

Não é necessário executar como administrador nem mudar a política de execução do PowerShell.

### 4. Use a página

O navegador abrirá no endereço exibido pela janela, geralmente **http://127.0.0.1:5500**.

1. Na primeira utilização, clique em **Criar conta**.
2. Preencha nome, e-mail e senha. Para testes locais, você pode usar um e-mail fictício com formato válido; o programa não envia e-mail de confirmação.
3. Crie um treino e uma refeição para montar seu mural.
4. No desktop, abra “Conexão dos serviços” para conferir os indicadores Python e Java.

### Usando os novos controles

- **Dia da semana:** clique no botão com o dia e escolha um dos sete balões. No mural, o botão “Semana toda” abre o mesmo seletor para filtrar os cards.
- **Grupos musculares:** marque quantos grupos quiser. Para incluir outro, abra “Grupo personalizado”, digite o nome e use “Salvar grupo”. Ele fica disponível na sua conta.
- **Exercícios:** escolha uma opção conhecida na lista. “Exercício personalizado” permite cadastrar um nome que ficará disponível nos próximos treinos.
- **Técnica avançada:** o campo é opcional e fica dentro de cada exercício; você pode escolher uma técnica conhecida ou informar outra.
- **Cardio:** use “+ Cardio” e informe atividade, duração e intensidade. A distância é opcional. Você pode marcar a conclusão no próprio card.
- **Conexão das APIs:** no desktop, os indicadores ficam na área “Conexão dos serviços”, na lateral.

Ao atualizar o projeto com o programa aberto, pressione Enter na janela antiga
para encerrar e abra `INICIAR.cmd` novamente. Os dados permanecem na mesma pasta.

Se uma porta estiver ocupada, o iniciador escolhe outra e configura a página sozinho. Use o **endereço mostrado na janela**, que pode ser diferente do exemplo. Não é preciso editar nenhum arquivo.

### 5. Encerre com Enter

Mantenha a janela do iniciador aberta durante o uso. Para encerrar, volte a ela e **pressione Enter**. Isso para as duas APIs e o servidor da página que aquela janela iniciou.

Fechar apenas a aba do navegador não encerra os servidores. Para iniciar novamente, abra `INICIAR.cmd` outra vez. Seus dados continuam salvos na mesma pasta.

## Se preferir usar um comando

Abra um terminal **na pasta que contém `iniciar.py`** e execute:

```powershell
python iniciar.py
```

Se o seu Windows usa o comando `py`:

```powershell
py -3 iniciar.py
```

Opções adicionais:

| Comando | Quando usar |
| --- | --- |
| `python iniciar.py --no-browser` | Iniciar sem abrir uma nova aba automaticamente; copie o endereço mostrado. |
| `python iniciar.py --reparar` | Reinstalar as dependências Python e recompilar a Java. Requer internet caso haja downloads. |
| `python iniciar.py --smoke-test` | Testar se as duas APIs e a página iniciam corretamente e, em seguida, encerrar tudo. |

No Windows, essas opções também funcionam com `INICIAR.cmd`, por exemplo `INICIAR.cmd --reparar`, quando chamado pelo terminal.

## Problemas comuns

| O que aconteceu | Como resolver |
| --- | --- |
| “Python não encontrado” | Instale o Python pelo link acima, habilite o PATH quando essa opção existir e reabra o terminal. Tente `py -3 iniciar.py`. |
| “JDK 17 ou superior não encontrado” | Instale o **JDK**, não apenas o JRE. Confira JAVA_HOME/PATH e reabra o terminal. |
| A preparação falhou ao baixar dependências | Verifique a conexão e os arquivos em `.local/logs`. Tente iniciar novamente; se necessário, use `--reparar`. |
| O navegador não abriu | Copie o endereço que aparece depois de “Tudo pronto! Acesse”. |
| Você abriu `frontend/index.html` diretamente | Feche essa aba e use o endereço HTTP exibido pelo iniciador. |
| “O iniciador desta pasta já está aberto” | Use a janela já aberta. Se ela foi encerrada à força, reinicie o computador para encerrar os processos restantes e exclua **somente a pasta vazia `.local/inicializacao.lock`** antes de tentar de novo. Não apague os demais dados. |
| Uma API não iniciou | Veja `.local/logs/api-python.log` ou `.local/logs/api-java.log`. As mensagens de preparação ficam nos outros arquivos dessa mesma pasta. |
| A sessão expirou ou você atualizou uma versão antiga | Faça login novamente. |

O iniciador não encerra outros aplicativos para liberar portas. Se surgir um conflito durante a própria inicialização, ele informa o erro; basta executar novamente para escolher portas livres.

## Onde ficam os dados

- Contas e refeições: `api-python/fatoutfitin.db`.
- Treinos: `api-java/data/treinos.json`.
- Grupos e exercícios personalizados: `api-java/data/catalogo-personalizado.json`.
- Chave local das sessões: `.local/auth-secret`.
- Registros da inicialização: `.local/logs/`.

Para preservar os dados em outra máquina ou pasta, mantenha uma cópia de seus arquivos de dados. O ZIP do código não inclui contas, treinos, refeições, ambiente virtual, bibliotecas baixadas ou chaves. Ao extrair o pacote pela primeira vez, crie uma conta nova.

## Apresentação do trabalho

O comando único inicia os três componentes. Para o vídeo, mostre as mensagens da janela e a página em funcionamento. Use a aba **Network/Rede** do navegador para mostrar chamadas às duas APIs; as portas efetivas aparecem na janela e nos endereços das requisições.

Se quiser mostrar cada componente iniciando em um terminal separado, siga a seção **Execução manual** do README. No modo manual, as portas padrão são Python 5000, Java 8080 e página 5500; pode ser necessário ajustar conflitos manualmente.
