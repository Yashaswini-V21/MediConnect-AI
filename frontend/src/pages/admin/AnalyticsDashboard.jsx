/**
 * AnalyticsDashboard.jsx - M4 + M6
 * Recharts visualizations for both Admin and System-wide metrics.
 */
import React, { useState, useEffect } from 'react';
import { 
  LineChart, Line, AreaChart, Area, PieChart, Pie, Cell, 
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, BarChart, Bar
} from 'recharts';
import { useAdminAuth } from '../../context/AdminAuthContext';

const COLORS = ['#10b981', '#f59e0b', '#ef4444', '#6366f1'];

export default function AnalyticsDashboard() {
  const { adminFetch } = useAdminAuth();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    adminFetch('/analytics/trends?days=30')
      .then(res => {
        setData(res);
        setLoading(false);
      })
      .catch(err => {
        console.error("Failed to load analytics", err);
        setLoading(false);
      });
  }, [adminFetch]);

  if (loading) return <div className="p-8 text-white">Loading Trends...</div>;

  return (
    <div className="p-6 space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        
        {/* Trend Chart */}
        <div className="bg-gray-800 p-6 rounded-xl border border-gray-700 shadow-xl">
          <h3 className="text-gray-400 text-sm font-medium mb-4 uppercase tracking-wider">Appointment Trends</h3>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={data?.daily_trends}>
              <defs>
                <linearGradient id="colorTotal" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#10b981" stopOpacity={0.1}/>
                  <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="date" stroke="#9ca3af" fontSize={10} />
              <YAxis stroke="#9ca3af" fontSize={10} />
              <Tooltip 
                contentStyle={{ backgroundColor: '#1f2937', border: 'none', borderRadius: '8px' }}
                itemStyle={{ color: '#fff' }}
              />
              <Area type="monotone" dataKey="total" stroke="#10b981" fillOpacity={1} fill="url(#colorTotal)" />
              <Area type="monotone" dataKey="confirmed" stroke="#6366f1" fillOpacity={0} />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Specialty Demand */}
        <div className="bg-gray-800 p-6 rounded-xl border border-gray-700 shadow-xl">
          <h3 className="text-gray-400 text-sm font-medium mb-4 uppercase tracking-wider">Specialty Demand</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={Object.entries(data?.specialty_demand || {}).map(([name, count]) => ({ name, count }))}>
              <XAxis dataKey="name" stroke="#9ca3af" fontSize={10} />
              <YAxis stroke="#9ca3af" fontSize={10} />
              <Tooltip contentStyle={{ backgroundColor: '#1f2937', border: 'none' }} />
              <Bar dataKey="count" fill="#3b82f6" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

      </div>
    </div>
  );
}
