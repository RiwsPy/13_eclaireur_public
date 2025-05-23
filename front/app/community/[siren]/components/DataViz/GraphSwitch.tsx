import { ReactNode } from 'react';

import { Switch } from '@/components/ui/switch';

type GraphSwitchProps = {
  label1: ReactNode;
  label2: ReactNode;
  isActive: boolean;
  onChange: (value: boolean) => void;
};

function getCursorClassName(isActive: boolean) {
  return `cursor-pointer ${isActive ? 'text-neutral-400' : 'text-neutral-800'}`;
}

export function GraphSwitch({ label1, label2, isActive, onChange }: GraphSwitchProps) {
  return (
    <div className='flex items-baseline gap-2'>
      <div
        onClick={() => {
          onChange(false);
        }}
        className={getCursorClassName(isActive)}
      >
        ({label1}
      </div>
      <Switch
        checked={isActive}
        onCheckedChange={() => {
          onChange(!isActive);
        }}
      />
      <div
        onClick={() => {
          onChange(true);
        }}
        className={getCursorClassName(!isActive)}
      >
        {label2})
      </div>
    </div>
  );
}
