import {test,expect} from '@playwright/test';

for(const viewport of [{width:1024,height:768},{width:390,height:844}]){
  test(`reaches lower navigation and returns to input at ${viewport.width}x${viewport.height}`,async({page})=>{
    await page.setViewportSize(viewport);
    await page.goto('/');
    const growth=page.getByRole('button',{name:'08 성장 연구 3D',exact:true});
    await growth.click();
    await expect(growth).toHaveAttribute('aria-current','page');
    const box=await growth.boundingBox();
    expect(box).not.toBeNull();
    expect(box!.y).toBeGreaterThanOrEqual(0);
    expect(box!.y+box!.height).toBeLessThanOrEqual(viewport.height);
    expect(box!.x).toBeGreaterThanOrEqual(0);
    expect(box!.x+box!.width).toBeLessThanOrEqual(viewport.width);
    const input=page.getByRole('button',{name:'01 입력 설정',exact:true});
    await input.click();
    await expect(input).toHaveAttribute('aria-current','page');
    expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
  });
}
