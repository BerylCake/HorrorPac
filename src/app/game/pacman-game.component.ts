import { ChangeDetectionStrategy, Component } from '@angular/core';

@Component({
  selector: 'app-pacman-game',
  template: `
    <div class="game-shell">
      <h1 class="title">Pac-Man</h1>
      <p class="hint">Game canvas will mount here.</p>
    </div>
  `,
  styleUrl: './pacman-game.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class PacmanGameComponent {}
