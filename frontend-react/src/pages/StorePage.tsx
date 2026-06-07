import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { ShoppingCart } from 'lucide-react';

const StorePage = () => {
  const [items, setItems] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchItems = async () => {
      try {
        const response = await axios.get('/api/items');
        setItems(response.data);
      } catch (error) {
        console.error('Error fetching store items:', error);
      } finally {
        setLoading(false);
      }
    };
    fetchItems();
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-secondary-900">Hebrew Store</h1>
        <button className="bg-primary-50 text-primary-600 px-4 py-2 rounded-md font-medium hover:bg-primary-100 transition-colors flex items-center gap-2">
          <ShoppingCart size={20} />
          Cart (0)
        </button>
      </div>

      {loading ? (
        <div className="text-secondary-500">Loading items...</div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {items.length === 0 ? (
            <div className="col-span-full text-center py-12 text-secondary-500 bg-surface rounded-lg border border-secondary-100 shadow-soft">
              No items available in the store right now.
            </div>
          ) : (
            items.map((item) => (
              <div key={item.id} className="bg-surface rounded-lg border border-secondary-100 shadow-soft overflow-hidden flex flex-col">
                <div className="aspect-square bg-secondary-50 flex items-center justify-center p-4">
                  {/* Placeholder for item image */}
                  <div className="text-secondary-300 font-hebrew text-4xl">{item.title?.charAt(0)}</div>
                </div>
                <div className="p-4 flex-1 flex flex-col">
                  <h3 className="text-lg font-semibold text-secondary-900 font-hebrew">{item.title}</h3>
                  <p className="text-secondary-500 text-sm mt-1 mb-4 flex-1">{item.description}</p>
                  <div className="flex items-center justify-between mt-auto">
                    <span className="text-lg font-bold text-primary-600">${item.price}</span>
                    <button className="bg-primary-600 text-white px-3 py-1.5 rounded text-sm font-medium hover:bg-primary-700 transition-colors">
                      Add to Cart
                    </button>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
};

export default StorePage;
