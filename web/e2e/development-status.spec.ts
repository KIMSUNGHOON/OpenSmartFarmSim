import {test,expect} from '@playwright/test';
import {readFileSync} from 'node:fs';

test('wraps long development evidence at a narrow viewport and doubled text',async({page})=>{
  const record=JSON.parse(readFileSync(new URL('../public/development-status.json',import.meta.url),'utf8'));
  const evidence='stored-crop-catalogue/current-reader/version-and-verification/'.repeat(3);
  record.reported_at=new Date().toISOString().replace('Z','000Z');
  record.stages[0].evidence=evidence;
  await page.route('**/development-status.json',route=>route.fulfill({json:record}));
  await page.setViewportSize({width:320,height:900});
  await page.goto('/');
  const status=page.getByRole('region',{name:'제품 개발과 배포 상태',exact:true});
  await expect(status.getByText(evidence,{exact:false})).toBeVisible();
  await page.addStyleTag({content:':root{font-size:32px}'});
  await page.evaluate(()=>document.fonts.ready);
  expect(await page.evaluate(()=>document.documentElement.scrollWidth)).toBeLessThanOrEqual(320);
  await expect(status.getByText(evidence,{exact:false})).toBeVisible();
});
