import FranceMap from '@/components/FranceMap';

export default async function MapPage() {
  return (
    <div className='min-h-screen'>
      <div style={{ width: '500px', height: '500px' }}>
        <FranceMap width={500} height={500} />
      </div>
    </div>
  );
}
