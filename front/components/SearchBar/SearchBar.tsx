'use client';

import { ChangeEvent, useState } from 'react';

import { Community } from '@/app/models/community';
import { debounce } from '@/utils/utils';
import { Search } from 'lucide-react';

import { Input } from '../ui/input';
import Suggestions from './SearchSuggestions';

type SearchBarProps = {
  onSelect: (picked: Pick<Community, 'nom' | 'siren' | 'type' | 'code_postal'>) => void;
};

export default function SearchBar({ onSelect }: SearchBarProps) {
  const [query, setQuery] = useState('');
  const [isFocused, setIsFocused] = useState(false);

  function handleOnFocus() {
    setIsFocused(true);
  }
  function handleOnBlur() {
    setTimeout(() => setIsFocused(false), 200);
  }

  const handleInputChange = debounce(
    (event: ChangeEvent<HTMLInputElement>) => setQuery(event.target.value),
    400,
  );
  const showSuggestions = query.length > 0 && isFocused;

  return (
    <div className='relative w-4/5'>
      <div className='relative'>
        <Search className='absolute left-2 top-1/2 h-4 w-4 -translate-y-1/2 transform text-muted-foreground' />
        <Input
          className='pl-8 pr-4'
          placeholder='Rechercher par Code postal, Commune, Département, Région'
          onChange={handleInputChange}
          onFocus={handleOnFocus}
          onBlur={(e) => {
            if (e.relatedTarget === null) handleOnBlur();
          }}
        />
      </div>
      {showSuggestions && <Suggestions query={query} onSelect={onSelect} />}
    </div>
  );
}
