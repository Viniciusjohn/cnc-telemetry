# Decisões de Arquitetura - CNC-Genius Telemetria v0.1

## Separação de Responsabilidades

**cnc-telemetry** = serviço independente responsável por:
- Coleta de dados MTConnect
- Interface web de monitoramento
- Exposição de endpoint JSON canônico

**cnc-genius** (otimização de G-code) = não será modificado até o piloto M80 estar validado.

## Contrato de Dados

A telemetria expõe um endpoint JSON canônico (`/v1/machines/{id}/status`) que será consumido futuramente por:
- Módulos do CNC-Genius
- Aplicativo Android
- Outros sistemas de monitoramento

## Arquitetura Atual

```
MTConnect/Simulador → Backend FastAPI → Endpoint JSON → Frontend React
                                    ↓
                               TimescaleDB (histórico)
```

## Decisões Técnicas

- **Polling**: 1 segundo fixo para tempo real
- **Formato de dados**: JSON canônico v0.1 com campos opcionais tolerantes a null
- **UI**: Dashboard responsivo otimizado para 1920x1080
- **Branding**: CNC-Genius Telemetria (unificação da marca)

## Status do Projeto

- ✅ Base funcional existente (MTConnect + UI + API)
- 🔄 Migração para contrato v0.1 em andamento
- 📋 Layout final v0.1 pendente
- 🎨 Branding CNC-Genius em implementação
