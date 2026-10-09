import type {StoredCropSelection} from '../src/SelectedCropReplay';

declare global {
  interface Window {
    __showSelectedCrop:(token:string|null,selection:StoredCropSelection|null)=>void;
  }
}
