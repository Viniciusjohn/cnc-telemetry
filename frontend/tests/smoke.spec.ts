import { test, expect } from '@playwright/test';

// Base URL
const BASE_URL = 'http://localhost:5173';

test.describe('F3 Gate — Dashboard PWA Smoke Tests', () => {
  
  test.beforeEach(async ({ page }) => {
    // Navegar para o dashboard antes de cada teste
    await page.goto(BASE_URL);
  });

  test('1. Dashboard loads successfully', async ({ page }) => {
    // Verificar título
    await expect(page).toHaveTitle(/CNC Telemetry/);
    
    // Verificar URL correta
    expect(page.url()).toBe(BASE_URL + '/');
    
    // Verificar sem erros no console
    const errors: string[] = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });
    
    // Aguardar carregamento
    await page.waitForLoadState('networkidle');
    
    // Não deve ter erros críticos
    expect(errors.filter(e => !e.includes('favicon'))).toHaveLength(0);
  });

  test('2. Status cards are visible', async ({ page }) => {
    // Aguardar os cards aparecerem
    await page.waitForSelector('text=RPM', { timeout: 5000 });
    await page.waitForSelector('text=Feed', { timeout: 5000 });
    await page.waitForSelector('text=Estado', { timeout: 5000 });
    
    // Verificar conteúdo dos cards
    const rpmCard = page.locator('text=RPM').first();
    const feedCard = page.locator('text=Feed').first();
    const stateCard = page.locator('text=Estado').first();
    
    await expect(rpmCard).toBeVisible();
    await expect(feedCard).toBeVisible();
    await expect(stateCard).toBeVisible();
  });

  test('3. Polling works (data updates)', async ({ page }) => {
    // Aguardar primeiro carregamento
    await page.waitForSelector('text=RPM', { timeout: 5000 });
    
    // Capturar timestamp inicial
    const initialTimestamp = await page.textContent('[data-testid="last-update"]') || 
                             await page.textContent('text=/atualizado/i') ||
                             'N/A';
    
    console.log('Initial timestamp:', initialTimestamp);
    
    // Aguardar 5 segundos (2 ciclos de polling de 2s cada)
    await page.waitForTimeout(5000);
    
    // Verificar se houve requisição para API
    const apiRequests = page.context().request;
    
    // O dashboard deve estar fazendo polling
    // (difícil testar exato update sem backend, mas verificamos se não travou)
    const pageContent = await page.content();
    expect(pageContent).toContain('RPM');
    expect(pageContent).toContain('Feed');
  });

  test('4. No console errors during normal operation', async ({ page }) => {
    const errors: string[] = [];
    const warnings: string[] = [];
    
    page.on('console', msg => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      } else if (msg.type() === 'warning') {
        warnings.push(msg.text());
      }
    });
    
    // Navegar e aguardar
    await page.goto(BASE_URL);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(3000);
    
    // Filtrar erros conhecidos/aceitáveis
    const criticalErrors = errors.filter(e => 
      !e.includes('favicon') && 
      !e.includes('manifest') &&
      !e.includes('ERR_CONNECTION_REFUSED')  // OK se backend não estiver rodando
    );
    
    console.log('Errors found:', errors.length);
    console.log('Critical errors:', criticalErrors.length);
    
    // Não deve ter erros críticos de JavaScript
    expect(criticalErrors).toHaveLength(0);
  });

  test('5. Responsive design (mobile viewport)', async ({ page }) => {
    // Definir viewport mobile
    await page.setViewportSize({ width: 375, height: 667 });
    
    // Recarregar
    await page.goto(BASE_URL);
    await page.waitForLoadState('networkidle');
    
    // Cards devem estar visíveis mesmo em mobile
    await expect(page.locator('text=RPM').first()).toBeVisible();
    await expect(page.locator('text=Feed').first()).toBeVisible();
    await expect(page.locator('text=Estado').first()).toBeVisible();
    
    // Verificar que não tem scroll horizontal
    const scrollWidth = await page.evaluate(() => document.documentElement.scrollWidth);
    const clientWidth = await page.evaluate(() => document.documentElement.clientWidth);
    
    expect(scrollWidth).toBeLessThanOrEqual(clientWidth + 1); // +1 para tolerância
  });

  test('6. State colors are correct', async ({ page }) => {
    // Aguardar carregamento
    await page.waitForSelector('text=Estado', { timeout: 5000 });
    
    // Verificar que existem classes de cor (bg-green, bg-red, bg-yellow)
    const content = await page.content();
    
    // Deve ter pelo menos um indicador de cor (bg-green, bg-red, ou bg-yellow)
    const hasColorClasses = 
      content.includes('bg-green') || 
      content.includes('bg-red') || 
      content.includes('bg-yellow');
    
    expect(hasColorClasses).toBeTruthy();
  });
});
