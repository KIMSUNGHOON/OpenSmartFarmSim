import {test,expect} from '@playwright/test';
import {revealConnection} from './connection-fixture';

test('connection entry preserves the open form and reopens a closed form',async({page})=>{
  await page.goto('/');
  const token=page.getByLabel('접근 토큰');
  await expect(token).toBeVisible();
  await token.fill('owned-connection-entry-draft-only');
  await revealConnection(page);
  await expect(token).toHaveValue('owned-connection-entry-draft-only');
  await page.getByText('내부 시험 연결',{exact:true}).click();
  await expect(token).toBeHidden();
  await revealConnection(page);
  await expect(token).toBeVisible();
  await expect(token).toHaveValue('owned-connection-entry-draft-only');
});
