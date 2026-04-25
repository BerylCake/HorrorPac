import { Routes } from '@angular/router';
import { PacmanGameComponent } from './game/pacman-game.component';

export const routes: Routes = [
  { path: '', component: PacmanGameComponent },
  { path: '**', redirectTo: '' },
];
