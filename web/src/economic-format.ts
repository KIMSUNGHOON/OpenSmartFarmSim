export function money(value:string|null) {
  if(value===null)return '미확인';
  const [whole,fraction]=value.split('.');
  return (whole ?? '').replace(/\B(?=(\d{3})+(?!\d))/g,',')+(fraction===undefined ? '' : '.'+fraction)+' 원';
}
