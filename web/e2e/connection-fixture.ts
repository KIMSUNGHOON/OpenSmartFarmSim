import type {Page} from '@playwright/test';

export async function revealConnection(page:Page) {
  if(await page.locator('.connection').getAttribute('open')===null)
    await page.getByText('내부 시험 연결',{exact:true}).click();
  await page.getByLabel('접근 토큰').waitFor({state:'visible'});
}
