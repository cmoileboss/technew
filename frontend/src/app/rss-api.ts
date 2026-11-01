import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface Feed {
  id: number;
  url: string;
  title: string;
  last_fetched_at: string | null;
  last_error: string | null;
  article_count: number;
}

export interface Article {
  id: number;
  feed_id: number;
  feed_title: string;
  title: string;
  link: string;
  summary: string;
  published_at: string | null;
}

export interface ArticlePage {
  items: Article[];
  total: number;
}

export interface RefreshResult {
  new_articles: number;
  errors: number;
}

export interface ArticleQuery {
  feedId?: number | null;
  q?: string;
  limit?: number;
  offset?: number;
}

@Injectable({ providedIn: 'root' })
export class RssApi {
  private readonly http = inject(HttpClient);

  listFeeds(): Observable<Feed[]> {
    return this.http.get<Feed[]>('/api/feeds');
  }

  addFeed(url: string, title?: string): Observable<Feed> {
    return this.http.post<Feed>('/api/feeds', { url, title: title || null });
  }

  deleteFeed(id: number): Observable<void> {
    return this.http.delete<void>(`/api/feeds/${id}`);
  }

  refresh(): Observable<RefreshResult> {
    return this.http.post<RefreshResult>('/api/refresh', null);
  }

  listArticles(query: ArticleQuery): Observable<ArticlePage> {
    const params: Record<string, string | number> = {
      limit: query.limit ?? 20,
      offset: query.offset ?? 0,
    };
    if (query.feedId != null) params['feed_id'] = query.feedId;
    if (query.q?.trim()) params['q'] = query.q.trim();
    return this.http.get<ArticlePage>('/api/articles', { params });
  }
}
