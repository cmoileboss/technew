import { Component, OnInit, inject, signal } from '@angular/core';
import { DatePipe, DecimalPipe } from '@angular/common';
import { HttpErrorResponse } from '@angular/common/http';
import { FormsModule } from '@angular/forms';
import { Article, Feed, RssApi } from './rss-api';

const PAGE_SIZE = 20;

const THEME_LABELS: Record<string, string> = {
  'sécurité': 'Sécurité',
  framework: 'Framework',
  ia: 'IA',
  autre: 'Autre',
};

@Component({
  selector: 'app-root',
  imports: [FormsModule, DatePipe, DecimalPipe],
  templateUrl: './app.html',
  styleUrl: './app.css',
})
export class App implements OnInit {
  private readonly api = inject(RssApi);
  private searchTimer: ReturnType<typeof setTimeout> | undefined;
  private requestId = 0;

  protected readonly feeds = signal<Feed[]>([]);
  protected readonly articles = signal<Article[]>([]);
  protected readonly total = signal(0);
  protected readonly selectedFeedId = signal<number | null>(null);
  protected readonly selectedTheme = signal<string | null>(null);
  protected readonly themes = Object.entries(THEME_LABELS).map(([value, label]) => ({ value, label }));
  protected readonly loading = signal(false);
  protected readonly refreshing = signal(false);
  protected readonly message = signal<{ kind: 'info' | 'error'; text: string } | null>(null);

  protected query = '';
  protected newUrl = '';
  protected newTitle = '';

  ngOnInit(): void {
    this.loadFeeds();
    this.loadArticles(true);
  }

  protected selectFeed(id: number | null): void {
    this.selectedFeedId.set(id);
    this.loadArticles(true);
  }

  protected selectTheme(theme: string | null): void {
    this.selectedTheme.set(theme);
    this.loadArticles(true);
  }

  protected themeLabel(theme: string): string {
    return THEME_LABELS[theme] ?? theme;
  }

  protected onSearch(): void {
    clearTimeout(this.searchTimer);
    this.searchTimer = setTimeout(() => this.loadArticles(true), 300);
  }

  protected loadMore(): void {
    this.loadArticles(false);
  }

  protected addFeed(): void {
    const url = this.newUrl.trim();
    if (!url) return;
    this.message.set({ kind: 'info', text: 'Ajout du flux en cours…' });
    this.api.addFeed(url, this.newTitle.trim()).subscribe({
      next: (feed) => {
        this.newUrl = this.newTitle = '';
        this.message.set({ kind: 'info', text: `Flux « ${feed.title} » ajouté (${feed.article_count} articles).` });
        this.loadFeeds();
        this.loadArticles(true);
      },
      error: (err) => this.fail(err),
    });
  }

  protected removeFeed(feed: Feed): void {
    if (!confirm(`Supprimer le flux « ${feed.title} » et ses articles ?`)) return;
    this.api.deleteFeed(feed.id).subscribe({
      next: () => {
        if (this.selectedFeedId() === feed.id) this.selectedFeedId.set(null);
        this.loadFeeds();
        this.loadArticles(true);
      },
      error: (err) => this.fail(err),
    });
  }

  protected refresh(): void {
    this.refreshing.set(true);
    this.api.refresh().subscribe({
      next: (res) => {
        this.refreshing.set(false);
        const errors = res.errors ? ` — ${res.errors} flux en erreur` : '';
        this.message.set({
          kind: res.errors ? 'error' : 'info',
          text: `${res.new_articles} nouvel(s) article(s)${errors}.`,
        });
        this.loadFeeds();
        this.loadArticles(true);
      },
      error: (err) => {
        this.refreshing.set(false);
        this.fail(err);
      },
    });
  }

  private loadFeeds(): void {
    this.api.listFeeds().subscribe({
      next: (feeds) => this.feeds.set(feeds),
      error: (err) => this.fail(err),
    });
  }

  private loadArticles(reset: boolean): void {
    const id = ++this.requestId;
    const offset = reset ? 0 : this.articles().length;
    this.loading.set(true);
    this.api
      .listArticles({
        feedId: this.selectedFeedId(),
        theme: this.selectedTheme(),
        q: this.query,
        limit: PAGE_SIZE,
        offset,
      })
      .subscribe({
        next: (page) => {
          if (id !== this.requestId) return;
          this.articles.set(reset ? page.items : [...this.articles(), ...page.items]);
          this.total.set(page.total);
          this.loading.set(false);
        },
        error: (err) => {
          if (id !== this.requestId) return;
          this.loading.set(false);
          this.fail(err);
        },
      });
  }

  private fail(err: unknown): void {
    const detail = err instanceof HttpErrorResponse ? err.error?.detail : null;
    const text = typeof detail === 'string' ? detail : "Impossible de joindre l'API (le backend est-il démarré ?).";
    this.message.set({ kind: 'error', text });
  }
}
