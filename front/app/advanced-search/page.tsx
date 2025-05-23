'use client';

import { Suspense } from 'react';

import Loading from '@/components/ui/Loading';
import { useAdvancedSearch } from '@/utils/hooks/useAdvancedSearch';

import { AdvancedSearchTable } from './components/AdvanceSearchTable';
import DownloadingButton from './components/DownloadingButton';
import { Filters } from './components/Filters/Filters';
import GoBackHome from './components/GoBackHome';
import { NeedFilterValue } from './components/NeedFilterValue';
import { NoResults } from './components/NoResults';
import { useFiltersParams } from './hooks/useFiltersParams';
import { useOrderParams } from './hooks/useOrderParams';
import { usePaginationParams } from './hooks/usePaginationParams';

export default function Page() {
  return (
    <div className='global-margin my-20 flex flex-col gap-x-10 gap-y-5'>
      <GoBackHome />
      <h1 className='text-2xl font-bold'>Recherche Avancée</h1>
      <Suspense fallback={<Loading />}>
        <div className='flex items-end justify-between'>
          <Filters />
          <DownloadingButton />
        </div>
      </Suspense>
      <Suspense fallback={<Loading />}>
        <CommunitiesTableWithLoader />
      </Suspense>
    </div>
  );
}

function CommunitiesTableWithLoader() {
  const { filters } = useFiltersParams();
  const { pagination } = usePaginationParams();
  const { order } = useOrderParams();

  const { data } = useAdvancedSearch(filters, pagination, order);

  if (Object.values(filters).every((x) => x == null)) {
    return <NeedFilterValue />;
  }

  if (!data) return <Loading />;

  if (data && data.length > 0) {
    return <AdvancedSearchTable communities={data} />;
  }

  return <NoResults />;
}
