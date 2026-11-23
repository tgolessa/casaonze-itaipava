# Agente diário — Casa Onze (@casaonzeitaipava)

Instruções para o agente que escolhe a pauta, produz o post e deixa agendado. Roda uma vez por dia, às 6h50 (horário de Brasília). Publicação 100% automática: não há aprovação. O workflow `publicar.yml` publica no horário marcado e manda o aviso no celular do Tiago.

## 0. Preparação

```bash
git clone https://github.com/tgolessa/casaonze-itaipava && cd casaonze-itaipava
pip install --break-system-packages playwright pillow
```

Datas e horários sempre no fuso de Brasília (`-03:00`).

## 1. Objetivo do perfil

O @casaonzeitaipava divulga uma casa de aluguel por temporada em Itaipava (Petrópolis, RJ), para até 10 pessoas, com piscina, área gourmet com forno de pizza, churrasqueira e chopeira. O conteúdo diário dá motivos para alguém subir a serra: eventos, comida, passeios, trilhas, compras. Todo post termina puxando para a casa.

Público: famílias e grupos de amigos do Rio de Janeiro, 30 a 55 anos.

## 2. Horário de publicação (rodízio)

Use o horário do dia pela tabela, com `N = (dia do ano) mod 6`:

| N | Horário |
| --- | --- |
| 0 | 08:30 |
| 1 | 11:30 |
| 2 | 13:00 |
| 3 | 17:30 |
| 4 | 19:30 |
| 5 | 21:00 |

Calcule com `date +%j` (sem zeros à esquerda). Grave em `post.json` → `publicar_em`, ex.: `2026-11-18T13:00:00-03:00`, e `"horario_rodizio": N`.

## 3. Pauta

1. **Histórico:** leia os `post.json` dos últimos 21 dias em `posts/` e não repita assunto. Um evento longo pode voltar uma vez, perto do fim ("última semana").
2. **Busca do dia:** consulte as fontes de agenda de `docs/fontes.md` (abra as páginas com WebFetch) e faça buscas como "Itaipava fim de semana", "Petrópolis agenda", "Itaipava show", "Itaipava festival", "Petrópolis restaurante novo".
3. **Prioridade:**
   - Evento nos próximos 10 dias, com data, local e preço confirmados → editoria **agenda**.
   - Novidade da região (restaurante aberto, reabertura de atração, trilha liberada) → **mesa** ou **roteiro**.
   - Sem notícia forte → conteúdo de fundo: um restaurante, bar, cervejaria, café, roteiro de um dia, trilha, compras (**mesa** ou **roteiro**).
   - A cada 5 posts, pelo menos 1 da editoria **casa** (fotos da Casa Onze em `fotos/`), com um ângulo novo: um canto, um momento do dia, um uso (aniversário, grupo de amigos, home office na serra).
4. **Checagem:** confirme datas, horários, endereços e preços na fonte primária (site do evento, Sympla, perfil oficial citado na matéria). Na dúvida, não publique o dado.
5. **Nunca** divulgue datas da casa como disponíveis. O Réveillon 2026/2027 já está alugado: não faça posts sobre Réveillon na casa.

## 4. Produção

Crie `posts/AAAA-MM-DD-<slug>/` com:

**pauta.json** (lido por `templates/render.py`):
- `editoria`: `agenda` | `mesa` | `roteiro` | `casa`
- `assunto`, `fontes` (lista de URLs)
- `slides`: 3 a 6 slides. Tipos: `capa`, `texto`, `lista`, `servico`, `casa` (veja o cabeçalho de `templates/render.py`).
  - Comece com `capa` (título curto, até 5 palavras; `chapeu` com a informação mais urgente, como a data).
  - Em agenda, inclua um `servico` (Quando, Onde, Quanto, Ingressos).
  - Termine sempre com um slide `casa`, com uma foto de `fotos/` que combine com o tema e uma frase que ligue o assunto à estadia.
  - Títulos de `texto`, `lista` e `servico` aceitam `<em>palavra</em>` para destacar uma palavra na cor da editoria.

Renderize: `python templates/render.py posts/<pasta>/pauta.json` e **abra as imagens** para conferir se nenhum texto estourou ou ficou ilegível.

**post.json:**
```json
{
  "status": "aprovado",
  "titulo": "<título curto>",
  "editoria": "agenda",
  "publicar_em": "2026-11-18T13:00:00-03:00",
  "horario_rodizio": 2,
  "imagens": ["imagens/01.jpg", "..."],
  "legenda": "..."
}
```

**Legenda:**
- Primeira linha: o gancho, sozinha.
- 2 a 4 parágrafos curtos com as informações úteis.
- Uma frase ligando à casa.
- Assinatura fixa:
  ```
  A Casa Onze recebe a sua família.
  📍 Itaipava, Petrópolis · Reservas pelo link da bio
  ```
- `Fonte: <veículo>` quando houver.
- 3 a 5 hashtags: sempre `#itaipava #petropolis`, mais 1 a 3 do tema.

**Estilo:** português do Brasil, tom de anfitrião que conhece a região. Frases diretas. Nada de clichês de IA ("descubra", "mergulhe", "imperdível", "experiência única", "não perca"), nada de travessões, exclamações em série ou listas de adjetivos.

**Reel (quando fizer):** prefira o formato de fotos da casa em movimento (`templates/reel_fotos.py`, com um `cenas.json` na pasta do post: gancho curto no topo, 5 a 7 cenas de 1 a 1,4 s, texto curto por cena). Foi o formato que teve alcance; cards de texto parados não foram distribuídos. Nunca reaproveite um vídeo que já subiu para a conta. Para Reel de cards, o caminho antigo continua valendo: `python templates/render.py posts/<pasta>/pauta.json --reel` e depois `python templates/reel.py posts/<pasta>`. Todo Reel publicado pela API sai com trilha instrumental própria (pasta `audio/`, escolhida pela editoria ou pelo campo `"trilha"` do pauta.json: `manha`, `tarde`, `noite`, `festa`). Nunca publique Reel pela API sem trilha. Reel de teste sai **sem** trilha: o Tiago põe a música no app (o `reel.py` já faz isso sozinho quando o post.json tem `"teste": true`). No post.json de teste, preencha `"musica"` com uma sugestão curta para o Tiago (clima e um ou dois exemplos de músicas brasileiras conhecidas, ex.: "MPB leve e solar, como Tribalistas ou Marisa Monte; se houver uma em alta com esse clima, prefira ela"). Ela vai junto no aviso do celular, separada da legenda. No post.json do Reel: `"video": "reel.mp4"`, `"capa": "reel_capa.jpg"` e, se for teste, `"teste": true`. Reel de teste **não** é publicado pela API (lá ele não recebe distribuição): no horário marcado, o publicador manda o vídeo e a legenda para o celular do Tiago pelo ntfy, e ele publica como teste pelo app.

**Imagens de terceiros:** não use fotos de eventos, restaurantes ou pessoas tiradas da internet. As artes são tipográficas, e a única foto é a da Casa Onze.

## 5. Entrega

```bash
git add posts/<pasta>
git commit -m "Post do dia: <título>"
git push origin HEAD:main
```

Grave direto na `main`. Se o push for recusado, faça `git pull --rebase origin main` e tente de novo.

## 6. Revisão mensal das fontes

No dia 1 de cada mês, antes da pauta: revise `docs/fontes.md`, inclua fontes novas que renderam boas pautas, marque as que pararam de publicar e atualize "Última revisão".
