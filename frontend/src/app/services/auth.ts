import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { Observable, tap } from 'rxjs';

@Injectable({
  providedIn: 'root',
})
export class Auth {
  private apiUrl = 'http://127.0.0.1:8000/auth';

  constructor(private http: HttpClient, private router: Router) {}

  login(email: string, password: string): Observable<any> {
    return this.http.post(`${this.apiUrl}/login`, { email, password }).pipe(
      tap((response: any) => {
        this.setStorageItem('token', response.access_token);
        this.setStorageItem('nom', response.nom);
        this.setStorageItem('email', response.email);
      })
    );
  }

  logout(): void {
    this.removeStorageItem('token');
    this.removeStorageItem('nom');
    this.removeStorageItem('email');
    this.router.navigate(['/login']);
  }

  isLoggedIn(): boolean {
    return !!this.getStorageItem('token');
  }

  getToken(): string | null {
    return this.getStorageItem('token');
  }

  getNom(): string | null {
    return this.getStorageItem('nom');
  }

  getEmail(): string | null {
    return this.getStorageItem('email');
  }

  private getStorageItem(key: string): string | null {
    if (!this.hasBrowserStorage()) {
      return null;
    }
    return localStorage.getItem(key);
  }

  private setStorageItem(key: string, value: string): void {
    if (!this.hasBrowserStorage()) {
      return;
    }
    localStorage.setItem(key, value);
  }

  private removeStorageItem(key: string): void {
    if (!this.hasBrowserStorage()) {
      return;
    }
    localStorage.removeItem(key);
  }

  private hasBrowserStorage(): boolean {
    return typeof window !== 'undefined' && typeof localStorage !== 'undefined';
  }
}
