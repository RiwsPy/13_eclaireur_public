import { downloadURL } from '@/utils/downloader/downloadURL';

import { Pagination } from '../../types';

const baseURL = process.env.NEXT_PUBLIC_BASE_URL;
function getAPIRoute(communitySiren: string) {
  return `/api/communities/${communitySiren}/subventions/by_naf2/download`;
}

export function createSubventionsByNafCSVDownloadingURL(
  communitySiren: string,
  year: number | null,
  pagination?: Pagination,
): URL {
  const url = new URL(getAPIRoute(communitySiren), baseURL);

  if (year !== null) url.searchParams.append('year', year.toString());

  if (pagination) {
    const { page, limit } = pagination;
    url.searchParams.append('page', page.toString());
    url.searchParams.append('limit', limit.toString());
  }

  return url;
}

export function downloadSubventionsByNafCSV(
  ...params: Parameters<typeof createSubventionsByNafCSVDownloadingURL>
) {
  const url = createSubventionsByNafCSVDownloadingURL(...params);

  downloadURL(url);
}
