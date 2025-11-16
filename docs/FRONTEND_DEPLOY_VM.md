# CNC Telemetry — Frontend Deploy em VM Linux (Piloto)

Guia rápido para gerar o build estático do painel (Vite/React) e servir o `dist/` na mesma VM do backend.

## Pré-requisitos
- VM Linux pequena (Ubuntu Server LTS recomendado) já provisionada como descrito em `DEPLOY_BETA_VM.md`.
- Node.js 20+ e npm instalados.
- Backend rodando e acessível pelo IP fixo (ex.: `https://200.220.15.10:8000`).

## Variáveis de ambiente
- `frontend/.env.development`: `VITE_API_BASE=http://localhost:8000`
- `frontend/.env.production` (exemplo documental):
  ```bash
  VITE_API_BASE=https://200.220.15.10:8000
  ```
  Ajuste para o IP/porta reais antes do build.

## Build estático
```bash
cd /path/to/cnc-telemetry-main/frontend
npm install
npm run build
```
Saída: pasta `frontend/dist/` pronta para ser servida.

## Servindo com Nginx
Copiar o conteúdo de `dist/` para `/var/www/cnc-telemetry` (ou diretório similar) e usar um virtual host simples. Exemplo (HTTPS com certificado self-signed):

```nginx
server {
    listen 443 ssl;
    server_name 200.220.15.10;

    ssl_certificate     /etc/ssl/certs/cnc-telemetry.crt;
    ssl_certificate_key /etc/ssl/private/cnc-telemetry.key;

    root /var/www/cnc-telemetry;
    index index.html;

    location / {
        try_files $uri /index.html;
    }
}

server {
    listen 80;
    server_name 200.220.15.10;
    return 301 https://$host$request_uri;
}
```

## Fluxo de validação manual
1. Rodar `npm run build` localmente e garantir que não haja erros de TypeScript/Vite.
2. Subir preview local para smoke test:
   ```bash
   npm run preview -- --host 0.0.0.0 --port 4173
   ```
3. Acessar `http://<IP-VM>:4173` de outro dispositivo na rede.
4. Verificar no console do navegador que as requisições usam `VITE_API_BASE` (sem CORS quebrado).
5. Com API sem dados, UI deve exibir cards vazios/zerados sem erros.
6. Após copiar para `/var/www/cnc-telemetry`, reiniciar Nginx (`sudo systemctl restart nginx`).

## Nota sobre HTTPS self-signed
- Durante o piloto aceitaremos certificados self-signed.
- O navegador exibirá aviso de segurança — instruir o cliente a aceitar o risco para acessar `https://200.220.15.10/`.
- Planejar emissão de certificado oficial (Let's Encrypt ou similar) para fases futuras.
