import React from 'react';
import EtfCard, { EtfCardProps } from './EtfCard';

interface DashboardGridProps {
  items: EtfCardProps[];
}

const DashboardGrid: React.FC<DashboardGridProps> = ({ items }) => {
  if (!items || items.length === 0) {
    return (
      <div className="text-center py-20 bg-gray-50 rounded-2xl border border-dashed border-gray-200">
        <p className="text-gray-500">暂无市场监控数据</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 p-1">
      {items.map((item) => (
        <EtfCard key={`${item.symbol}-${item.date}`} data={item} />
      ))}
    </div>
  );
};

export default DashboardGrid;






