import {test,expect} from '@playwright/test';
import {revealConnection,revealConnectedControls} from './connection-fixture';

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

test('connection controls remain available for locks and account changes after connecting',async({page})=>{
  await page.goto('/');
  await revealConnection(page);
  const token=page.getByLabel('접근 토큰');
  await token.fill('owned-connection-entry-draft-only');
  await page.getByRole('button',{name:'연결 설정',exact:true}).click();
  await expect(token).toBeHidden();
  await revealConnectedControls(page);
  await expect(page.getByRole('button',{name:'연결 해제',exact:true})).toBeEnabled();
  await token.fill('owned-replacement-account-draft-only');
  await expect(token).toHaveValue('owned-replacement-account-draft-only');
});
