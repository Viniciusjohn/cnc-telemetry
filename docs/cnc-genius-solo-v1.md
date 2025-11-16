# CNC-Genius SOLO v1 — Diretriz Oficial

**Status:** Ativa  
**Data:** 2025-11-15  
**Owner:** Vinícius (único)  
**Escopo:** Produto CNC-Genius + Telemetria + Otimização + Apps + Infra + Comercial

---

## 1. Princípio Absoluto
- O CNC-Genius é 100% de propriedade e decisão do Vinícius.  
- Não existe sócio técnico, co-owner, equity compartilhado ou dependência estrutural de terceiros.  
- Participantes futuros serão sempre prestadores, nunca donos; executores, nunca decisores; apoio, nunca estratégia.  
- Diretriz irrevogável até nova ordem.

## 2. Missão Central
- Criar, validar e escalar o CNC-Genius como solopreneur, focando em:  
  - Telemetria industrial (Mitsubishi M7x/M8x primeiro).  
  - Otimização pós-CAM (feature futura).  
  - ROI técnico (tempo, desgaste, scrap).  
  - Piloto real na NovaTEC com o M80.

## 3. Foco Imediato — Nestor → NovaTEC
- Backend pronto.  
- UI exibindo dados.  
- Telemetria funcionando, IP configurado, MTConnect ativo.  
- Atualização a cada 1 segundo.  
- Zero dependência de terceiros.  
- Vinícius presente e responsável por todo o teste na máquina.

## 4. Papéis e Fronteiras Permanentes
### 4.1 Vinícius (owner + arquiteto)
Responsável absoluto por:
- Backend, infra, telemetria, contratos de API, lógica industrial.  
- Testes na máquina, decisões técnicas, roteiro de deploy, roadmap e MVPs.  
- Pitch, negociação, fechamento com clientes.  
- Manutenção do core, segurança, observabilidade e telemetria.

### 4.2 Terceiros (eventual)
- Apenas prestadores por tarefa específica.  
- Sem acesso ao core, sem decisão estratégica, sem voz em arquitetura ou roadmap.  
- Sem equity, sem responsabilidade em piloto.  
- Exemplos: ajustes pontuais de UI/design/CSS.

## 5. Arquitetura Permanente — CNC-Genius SOLO
- CNC-Telemetry: serviço independente, FastAPI, JSON canônico, MTConnect, UI própria.  
- Execução local (PC do cliente) com IP fixo configurável e polling de 1s.  
- Resiliente e sem acoplamento com CNC-Genius Otimização.  
- CNC-Genius Otimização fica congelado até validação do piloto M80.  
- Visão futura: “CNC-Genius Hub” com abas Telemetria + Otimização + ROI.

## 6. Modo Operacional — SOLO
- Toda decisão técnica, execução crítica, deploy, teste em campo, conversa com cliente, arquitetura e segurança ficam com Vinícius.  
- Terceiros jamais assumem partes essenciais.

## 7. Diretriz Comercial
- Produto industrial com teste real em fábrica.  
- Entrada via telemetria, expansão para otimização, ROI documentado.  
- Proposta profissional; sem promessas irreais; crescimento baseado no domínio industrial de Vinícius.  
- Sem depender de equipe.

## 8. Regra de Prioridade
- Priorizar absolutamente tudo que aproxima o piloto M80.  
- Pendências que não impactam o teste são secundárias.  
- Sem distrações, features novas desnecessárias, frentes de frontend pesadas ou complexidade extra.

## 9. Atualizações
- Apenas Vinícius pode alterar, revogar, ampliar ou versionar esta diretriz.

## 10. Nome Oficial
- Modelo solo referido como **CNC-Genius SOLO v1** (padrão) ou **VERSHIP v1** (“um homem, um produto, um mercado”).

---

**Documento oficial:** `docs/cnc-genius-solo-v1.md`
