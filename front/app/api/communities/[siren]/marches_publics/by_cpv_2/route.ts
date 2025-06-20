import { NextResponse } from 'next/server';

import { fetchMarchesPublicsByCPV2 } from '@/utils/fetchers/marches-publics/fetchMarchesPublicsByCPV2-server';
import { parseNumber } from '@/utils/utils';

const DEFAULT_LIMIT = 10;
const DEFAULT_PAGE = 1;

export async function GET(request: Request, { params }: { params: Promise<{ siren: string }> }) {
  try {
    const { siren } = await params;
    const { searchParams } = new URL(request.url);

    if (siren === undefined) {
      throw new Error('Siren is not defined');
    }

    const year = parseNumber(searchParams.get('year'));
    const page = parseNumber(searchParams.get('page')) ?? DEFAULT_PAGE;
    const limit = parseNumber(searchParams.get('limit')) ?? DEFAULT_LIMIT;
    const maxAmount = parseNumber(searchParams.get('maxAmount'));

    const pagination = {
      page,
      limit,
    };

    const data = await fetchMarchesPublicsByCPV2(
      siren,
      year ?? null,
      pagination,
      maxAmount ?? null,
    );

    return NextResponse.json(data);
  } catch (error) {
    console.error('Database error: ', error);
    return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 });
  }
}
