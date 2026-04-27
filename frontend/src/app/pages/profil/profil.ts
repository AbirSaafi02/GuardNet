import { ChangeDetectorRef, Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClient, HttpHeaders } from '@angular/common/http';

import { Auth } from '../../services/auth';

@Component({
  selector: 'app-profil',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './profil.html',
  styleUrl: './profil.css',
})
export class Profil {
  nom = '';
  email = '';

  ancienPassword = '';
  nouveauPassword = '';
  confirmPassword = '';

  successMessage = '';
  errorMessage = '';

  constructor(
    private http: HttpClient,
    private authService: Auth,
    private cdr: ChangeDetectorRef
  ) {
    this.nom = this.authService.getNom() || '';
    this.email = this.authService.getEmail() || '';
  }

  changerMotDePasse(): void {
    this.successMessage = '';
    this.errorMessage = '';

    if (this.nouveauPassword !== this.confirmPassword) {
      this.errorMessage = 'Les mots de passe ne correspondent pas !';
      this.cdr.detectChanges();
      return;
    }

    if (this.nouveauPassword.trim().length < 6) {
      this.errorMessage = 'Le mot de passe doit contenir au moins 6 caracteres !';
      this.cdr.detectChanges();
      return;
    }

    const token = this.authService.getToken();
    const headers = new HttpHeaders({ Authorization: `Bearer ${token}` });

    this.http
      .put(
        'http://127.0.0.1:8000/auth/change-password',
        {
          ancien_password: this.ancienPassword,
          nouveau_password: this.nouveauPassword,
        },
        { headers }
      )
      .subscribe({
        next: () => {
          this.successMessage = 'Mot de passe change avec succes !';
          this.ancienPassword = '';
          this.nouveauPassword = '';
          this.confirmPassword = '';
          this.cdr.detectChanges();
        },
        error: (err) => {
          this.errorMessage =
            err.error?.detail || 'Ancien mot de passe incorrect !';
          this.cdr.detectChanges();
        },
      });
  }
}
