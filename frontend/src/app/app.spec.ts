import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { App } from './app';

describe('App', () => {
  let http: HttpTestingController;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [App],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();
    http = TestBed.inject(HttpTestingController);
  });

  it('displays the fetched articles with links', () => {
    const fixture = TestBed.createComponent(App);
    fixture.detectChanges();

    http.expectOne('/api/feeds').flush([]);
    http.expectOne((r) => r.url === '/api/articles').flush({
      total: 1,
      items: [
        {
          id: 1,
          feed_id: 1,
          feed_title: 'Demo',
          title: 'Premier article',
          link: 'https://example.com/1',
          summary: 'Un résumé',
          published_at: '2025-11-01T10:00:00+00:00',
        },
      ],
    });
    fixture.detectChanges();

    const el = fixture.nativeElement as HTMLElement;
    const link = el.querySelector('article a') as HTMLAnchorElement;
    expect(link.textContent).toContain('Premier article');
    expect(link.href).toBe('https://example.com/1');
    expect(el.textContent).toContain('Un résumé');
    http.verify();
  });
});
