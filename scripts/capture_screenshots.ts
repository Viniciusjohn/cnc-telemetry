// scripts/capture_screenshots.ts
// Captura automática de screenshots para documentação

import { chromium } from '@playwright/test';
import * as path from 'path';
import * as fs from 'fs';

const BASE_URL = 'http://localhost:5173';
const SCREENSHOTS_DIR = path.join(__dirname, '..', 'docs', 'screenshots');

// Garantir que diretório existe
if (!fs.existsSync(SCREENSHOTS_DIR)) {
  fs.mkdirSync(SCREENSHOTS_DIR, { recursive: true });
}

async function captureScreenshots() {
  console.log('🚀 Iniciando captura de screenshots...');
  
  const browser = await chromium.launch();
  const context = await browser.newContext();
  const page = await context.newPage();

  try {
    // 1. Desktop - Running state
    console.log('📸 Capturando: Desktop - Running');
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.goto(BASE_URL);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000); // Aguardar dados carregarem
    await page.screenshot({ 
      path: path.join(SCREENSHOTS_DIR, 'dashboard-desktop-running.png'),
      fullPage: true
    });

    // 2. Desktop - Full page com scroll
    console.log('📸 Capturando: Desktop - Full page');
    await page.screenshot({ 
      path: path.join(SCREENSHOTS_DIR, 'dashboard-desktop-full.png'),
      fullPage: true
    });

    // 3. Desktop - Viewport only
    console.log('📸 Capturando: Desktop - Viewport');
    await page.screenshot({ 
      path: path.join(SCREENSHOTS_DIR, 'dashboard-desktop.png'),
      fullPage: false
    });

    // 4. Tablet
    console.log('📸 Capturando: Tablet');
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.goto(BASE_URL);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
    await page.screenshot({ 
      path: path.join(SCREENSHOTS_DIR, 'dashboard-tablet.png'),
      fullPage: true
    });

    // 5. Mobile
    console.log('📸 Capturando: Mobile');
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto(BASE_URL);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
    await page.screenshot({ 
      path: path.join(SCREENSHOTS_DIR, 'dashboard-mobile.png'),
      fullPage: true
    });

    // 6. Mobile landscape
    console.log('📸 Capturando: Mobile Landscape');
    await page.setViewportSize({ width: 667, height: 375 });
    await page.goto(BASE_URL);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
    await page.screenshot({ 
      path: path.join(SCREENSHOTS_DIR, 'dashboard-mobile-landscape.png'),
      fullPage: false
    });

    // 7. Dark mode (se suportado)
    console.log('📸 Capturando: Dark mode');
    await page.emulateMedia({ colorScheme: 'dark' });
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.goto(BASE_URL);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
    await page.screenshot({ 
      path: path.join(SCREENSHOTS_DIR, 'dashboard-dark-mode.png'),
      fullPage: false
    });

    console.log('✅ Screenshots capturados com sucesso!');
    console.log(`📁 Salvos em: ${SCREENSHOTS_DIR}`);

  } catch (error) {
    console.error('❌ Erro ao capturar screenshots:', error);
    throw error;
  } finally {
    await browser.close();
  }
}

// Executar
captureScreenshots()
  .then(() => {
    console.log('\n✅ Processo concluído!');
    process.exit(0);
  })
  .catch((error) => {
    console.error('\n❌ Processo falhou:', error);
    process.exit(1);
  });
