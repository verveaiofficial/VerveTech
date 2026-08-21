"";
"use client";

import React, { useState, useEffect } from 'react';

interface Product {
  id: number;
  name: string;
  category: string;
  price: number;
  rating: number;
  reviewsCount: number;
  image: string;
  description: string;
  specs: string[];
}

interface CartItem extends Product {
  quantity: number;
}

const PRODUCTS: Product[] = [
  {
    id: 1,
    name: "Verve Pulse Pro ANC Headphones",
    category: "Audio",
    price: 349,
    rating: 4.9,
    reviewsCount: 128,
    image: "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?auto=format&fit=crop&w=800&q=80",
    description: "Industry-leading active noise cancellation with 40-hour battery life and spatial audio architecture.",
    specs: ["Hybrid ANC", "Bluetooth 5.3", "40hr Battery", "Spatial Audio"]
  },
  {
    id: 2,
    name: "Verve Watch Ultra Titanium",
    category: "Wearables",
    price: 499,
    rating: 4.8,
    reviewsCount: 94,
    image: "https://images.unsplash.com/photo-1523275335684-37898b6baf30?auto=format&fit=crop&w=800&q=80",
    description: "Aerospace-grade titanium case with sapphire crystal display and advanced biometric health sensors.",
    specs: ["Titanium Case", "Sapphire Crystal", "ECG & SpO2", "Water Resistant 100m"]
  },
  {
    id: 3,
    name: "VerveBook Air M3 Laptop",
    category: "Computers",
    price: 1299,
    rating: 5.0,
    reviewsCount: 215,
    image: "https://images.unsplash.com/photo-1517336714731-489689fd1ca8?auto=format&fit=crop&w=800&q=80",
    description: "Ultralight powerhouse featuring the next-generation M3 chip, Retina XDR display, and fanless silent design.",
    specs: ["M3 Chip", "16GB Unified RAM", "512GB SSD", "18hr Battery"]
  },
  {
    id: 4,
    name: "Verve Arc 4K OLED Monitor",
    category: "Displays",
    price: 899,
    rating: 4.7,
    reviewsCount: 76,
    image: "https://images.unsplash.com/photo-1527443224154-c4a3942d3acf?auto=format&fit=crop&w=800&q=80",
    description: "Stunning 32-inch 4K OLED display with 144Hz refresh rate, HDR1000, and ultra-thin bezels.",
    specs: ["32-inch 4K OLED", "144Hz Refresh", "USB-C 90W PD", "Infinite Contrast"]
  },
  {
    id: 5,
    name: "Verve Crystal Mini Speaker",
    category: "Audio",
    price: 149,
    rating: 4.6,
    reviewsCount: 142,
    image: "https://images.unsplash.com/photo-1608043152269-423dbba4e7e1?auto=format&fit=crop&w=800&q=80",
    description: "360-degree immersive acoustic soundstage in a compact, machined aluminum chassis.",
    specs: ["360 Sound", "IP67 Waterproof", "15hr Battery", "Stereo Pairing"]
  },
  {
    id: 6,
    name: "Verve Snap Magnetic Charger",
    category: "Accessories",
    price: 79,
    rating: 4.9,
    reviewsCount: 310,
    image: "https://images.unsplash.com/photo-1622445275576-793733079247?auto=format&fit=crop&w=800&q=80",
    description: "Fast wireless charging stand engineered with precision alignment magnets and premium alloy finish.",
    specs: ["15W Fast Charge", "MagSafe Compatible", "Alloy Stand", "Braided Cable"]
  }
];

export default function StorePage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("All");
  const [cart, setCart] = useState<CartItem[]>([]);
  const [isCartOpen, setIsCartOpen] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);
  const [checkoutStep, setCheckoutStep] = useState<'cart' | 'shipping' | 'success'>('cart');
  const [promoCode, setPromoCode] = useState("");
  const [discount, setDiscount] = useState(0);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  const [shippingInfo, setShippingInfo] = useState({
    name: "",
    email: "",
    address: "",
    city: "",
    country: ""
  });

  useEffect(() => {
    if (toastMessage) {
      const timer = setTimeout(() => setToastMessage(null), 3000);
      return () => clearTimeout(timer);
    }
  }, [toastMessage]);

  const showToast = (msg: string) => {
    setToastMessage(msg);
  };

  const categories = ["All", "Audio", "Wearables", "Computers", "Displays", "Accessories"];

  const filteredProducts = PRODUCTS.filter(p => {
    const matchesCategory = selectedCategory === "All" || p.category === selectedCategory;
    const matchesSearch = p.name.toLowerCase().includes(searchQuery.toLowerCase()) || p.description.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesCategory && matchesSearch;
  });

  const addToCart = (product: Product, e?: React.MouseEvent) => {
    if (e) e.stopPropagation();
    setCart(prev => {
      const existing = prev.find(item => item.id === product.id);
      if (existing) {
        return prev.map(item => item.id === product.id ? { ...item, quantity: item.quantity + 1 } : item);
      }
      return [...prev, { ...product, quantity: 1 }];
    });
    showToast(`Added ${product.name} to cart`);
  };

  const updateQuantity = (id: number, delta: number) => {
    setCart(prev => {
      return prev.map(item => {
        if (item.id === id) {
          const newQty = item.quantity + delta;
          return newQty > 0 ? { ...item, quantity: newQty } : null;
        }
        return item;
      }).filter(Boolean) as CartItem[];
    });
  };

  const subtotal = cart.reduce((sum, item) => sum + item.price * item.quantity, 0);
  const shippingFee = subtotal > 100 || subtotal === 0 ? 0 : 15;
  const total = Math.max(0, subtotal - discount + shippingFee);

  const applyPromo = (e: React.FormEvent) => {
    e.preventDefault();
    if (promoCode.toUpperCase() === "VERVE10") {
      setDiscount(Math.round(subtotal * 0.1));
      showToast("Promo code applied: 10% OFF");
    } else {
      showToast("Invalid promo code (Try VERVE10)");
    }
  };

  const handleCheckoutSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!shippingInfo.name || !shippingInfo.email || !shippingInfo.address) {
      showToast("Please fill in all required shipping details.");
      return;
    }
    setCheckoutStep('success');
    setCart([]);
  };

  return (
    <div className="min-h-screen bg-white text-neutral-900 flex flex-col font-sans overflow-x-hidden">
      {toastMessage && (
        <div className="fixed bottom-4 left-4 right-4 sm:left-auto sm:right-6 z-50 bg-neutral-900 text-white px-6 py-3.5 rounded-2xl text-sm font-medium shadow-2xl animate-fade-in border border-neutral-800 text-center sm:text-left">
          {toastMessage}
        </div>
      )}

      <div className="bg-neutral-900 text-white text-[11px] sm:text-xs py-2.5 px-3 text-center tracking-wide font-medium leading-relaxed">
        Complimentary express shipping over $100 • Use code <span className="font-bold underline">VERVE10</span> for 10% off
      </div>

      <header className="sticky top-0 z-40 bg-white/90 backdrop-blur-md border-b border-neutral-200 transition-all">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 sm:h-20 flex items-center justify-between">
          <div className="flex items-center space-x-3 cursor-pointer" onClick={() => { setSelectedCategory("All"); setSearchQuery(""); }}>
            <span className="text-xl sm:text-2xl font-black tracking-tighter uppercase">Verve<span className="text-neutral-500">Tech</span></span>
          </div>

          <nav className="hidden md:flex items-center space-x-8 text-sm font-medium text-neutral-600">
            {categories.slice(0, 5).map(cat => (
              <button
                key={cat}
                onClick={() => setSelectedCategory(cat)}
                className={`transition-colors hover:text-neutral-900 ${selectedCategory === cat ? 'text-neutral-900 font-semibold underline underline-offset-8' : ''}`}
              >
                {cat}
              </button>
            ))}
          </nav>

          <div className="flex items-center space-x-3">
            <div className="relative hidden lg:block">
              <input
                type="text"
                placeholder="Search products..."
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
                className="bg-neutral-100 text-sm rounded-full pl-4 pr-10 py-2 focus:outline-none focus:ring-2 focus:ring-neutral-900 transition-all w-52 xl:w-64 text-neutral-900 border border-transparent focus:border-neutral-900"
              />
              <svg className="w-4 h-4 text-neutral-500 absolute right-3.5 top-2.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>

            <button
              onClick={() => { setIsCartOpen(true); setCheckoutStep('cart'); }}
              className="relative bg-neutral-900 hover:bg-neutral-800 text-white px-4 sm:px-5 py-2 sm:py-2.5 rounded-full text-xs sm:text-sm font-medium transition-all flex items-center space-x-2 shadow-sm hover:shadow"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" />
              </svg>
              <span className="hidden xs:inline">Cart</span>
              {cart.reduce((sum, item) => sum + item.quantity, 0) > 0 && (
                <span className="absolute -top-1.5 -right-1.5 bg-white text-neutral-900 border border-neutral-900 text-[10px] font-bold w-5 h-5 rounded-full flex items-center justify-center shadow-sm">
                  {cart.reduce((sum, item) => sum + item.quantity, 0)}
                </span>
              )}
            </button>

            <button
              onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
              className="md:hidden p-2 rounded-xl text-neutral-700 hover:bg-neutral-100 transition-all focus:outline-none"
              aria-label="Toggle menu"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                {isMobileMenuOpen ? (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                ) : (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                )}
              </svg>
            </button>
          </div>
        </div>

        {isMobileMenuOpen && (
          <div className="md:hidden bg-white border-b border-neutral-200 px-4 py-6 animate-fade-in space-y-4">
            <div className="relative">
              <input
                type="text"
                placeholder="Search products..."
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
                className="w-full bg-neutral-100 text-sm rounded-full pl-4 pr-10 py-3 focus:outline-none focus:ring-2 focus:ring-neutral-900 text-neutral-900"
              />
              <svg className="w-4 h-4 text-neutral-500 absolute right-4 top-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
            <div className="flex flex-col space-y-2 pt-2">
              {categories.map(cat => (
                <button
                  key={cat}
                  onClick={() => {
                    setSelectedCategory(cat);
                    setIsMobileMenuOpen(false);
                  }}
                  className={`text-left py-2.5 px-4 rounded-xl text-sm font-medium transition-all ${
                    selectedCategory === cat ? 'bg-neutral-900 text-white' : 'text-neutral-700 hover:bg-neutral-100'
                  }`}
                >
                  {cat}
                </button>
              ))}
            </div>
          </div>
        )}
      </header>

      <section className="relative bg-neutral-50 border-b border-neutral-200 py-16 sm:py-20 lg:py-28 overflow-hidden">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
          <div className="max-w-3xl">
            <span className="inline-block text-[11px] sm:text-xs font-bold uppercase tracking-widest bg-neutral-200 text-neutral-800 px-3.5 py-1.5 rounded-full mb-4 sm:mb-6">
              New Release 2025
            </span>
            <h1 className="text-3xl sm:text-5xl lg:text-7xl font-extrabold tracking-tight text-neutral-900 leading-[1.1] mb-4 sm:mb-6">
              Effortless tech for the modern life.
            </h1>
            <p className="text-base sm:text-xl text-neutral-600 mb-6 sm:mb-8 max-w-2xl font-normal">
              Precision-engineered audio, wearables, and computing designed with minimalist aesthetics and uncompromising performance.
            </p>
            <div className="flex flex-col sm:flex-row items-stretch sm:items-center space-y-3 sm:space-y-0 sm:space-x-4">
              <a
                href="#store"
                className="bg-neutral-900 hover:bg-neutral-800 text-white text-center px-8 py-3.5 sm:py-4 rounded-full font-semibold text-sm transition-all shadow-lg hover:shadow-xl"
              >
                Explore Collection
              </a>
              <button
                onClick={() => setSelectedProduct(PRODUCTS[0])}
                className="border border-neutral-300 hover:border-neutral-900 text-neutral-900 text-center px-8 py-3.5 sm:py-4 rounded-full font-semibold text-sm transition-all bg-white shadow-sm"
              >
                View Featured Spotlight
              </button>
            </div>
          </div>
        </div>
      </section>

      <main id="store" className="flex-grow max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 sm:py-16 w-full">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 sm:mb-12 border-b border-neutral-200 pb-6 space-y-4 md:space-y-0">
          <div>
            <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-neutral-900">Catalog</h2>
            <p className="text-sm text-neutral-500 mt-1">Showing {filteredProducts.length} high-performance products</p>
          </div>

          <div className="flex flex-wrap gap-2 w-full md:w-auto overflow-x-auto pb-2 md:pb-0 scrollbar-none">
            {categories.map(cat => (
              <button
                key={cat}
                onClick={() => setSelectedCategory(cat)}
                className={`px-4 py-2 rounded-full text-xs font-semibold whitespace-nowrap transition-all ${
                  selectedCategory === cat
                    ? 'bg-neutral-900 text-white shadow-md'
                    : 'bg-neutral-100 text-neutral-600 hover:bg-neutral-200'
                }`}
              >
                {cat}
              </button>
            ))}
          </div>
        </div>

        {filteredProducts.length === 0 ? (
          <div className="text-center py-20 sm:py-24 bg-neutral-50 rounded-2xl border border-neutral-200 px-4">
            <p className="text-base sm:text-lg font-medium text-neutral-700">No products found matching your criteria.</p>
            <button
              onClick={() => { setSelectedCategory("All"); setSearchQuery(""); }}
              className="mt-4 inline-block bg-neutral-900 text-white px-6 py-2.5 rounded-full text-sm font-medium"
            >
              Reset Filters
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 sm:gap-8">
            {filteredProducts.map(product => (
              <div
                key={product.id}
                onClick={() => setSelectedProduct(product)}
                className="group bg-white rounded-3xl border border-neutral-200 overflow-hidden hover:border-neutral-900 transition-all duration-300 flex flex-col cursor-pointer shadow-sm hover:shadow-xl"
              >
                <div className="relative aspect-square bg-neutral-100 overflow-hidden">
                  <img
                    src={product.image}
                    alt={product.name}
                    className="object-cover w-full h-full group-hover:scale-105 transition-transform duration-500"
                  />
                  <span className="absolute top-4 left-4 bg-white/90 backdrop-blur-sm text-neutral-900 text-xs font-bold px-3 py-1.5 rounded-full shadow-sm">
                    {product.category}
                  </span>
                </div>

                <div className="p-5 sm:p-6 flex flex-col flex-grow justify-between">
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center space-x-1 text-xs text-amber-500 font-bold">
                        <span>★</span>
                        <span className="text-neutral-900">{product.rating}</span>
                        <span className="text-neutral-400 font-normal">({product.reviewsCount})</span>
                      </div>
                      <span className="text-lg sm:text-xl font-extrabold text-neutral-900">${product.price}</span>
                    </div>
                    <h3 className="text-base sm:text-lg font-bold text-neutral-900 group-hover:text-neutral-600 transition-colors mb-2">
                      {product.name}
                    </h3>
                    <p className="text-xs sm:text-sm text-neutral-500 line-clamp-2 mb-4">
                      {product.description}
                    </p>
                  </div>

                  <div className="pt-4 border-t border-neutral-100 flex items-center justify-between">
                    <span className="text-xs font-semibold text-neutral-600">View Specs</span>
                    <button
                      onClick={(e) => addToCart(product, e)}
                      className="bg-neutral-900 hover:bg-neutral-800 text-white text-xs font-semibold px-4 py-2.5 rounded-full transition-all flex items-center space-x-1.5 shadow-sm"
                    >
                      <span>+ Add to Cart</span>
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>

      {selectedProduct && (
        <div className="fixed inset-0 z-50 bg-black/65 backdrop-blur-sm flex items-center justify-center p-3 sm:p-4 animate-fade-in overflow-y-auto">
          <div className="bg-white rounded-3xl max-w-3xl w-full overflow-hidden shadow-2xl relative my-auto max-h-[95vh] flex flex-col md:flex-row">
            <button
              onClick={() => setSelectedProduct(null)}
              className="absolute top-4 right-4 z-10 bg-white/90 backdrop-blur-sm hover:bg-neutral-100 text-neutral-900 w-10 h-10 rounded-full flex items-center justify-center transition-all shadow-md font-bold"
            >
              ✕
            </button>

            <div className="md:w-1/2 bg-neutral-100 relative aspect-square md:aspect-auto">
              <img
                src={selectedProduct.image}
                alt={selectedProduct.name}
                className="object-cover w-full h-full"
              />
            </div>

            <div className="md:w-1/2 p-6 sm:p-8 flex flex-col justify-between overflow-y-auto max-h-[60vh] md:max-h-none">
              <div>
                <span className="text-xs font-bold uppercase tracking-wider bg-neutral-100 text-neutral-800 px-3.5 py-1.5 rounded-full">
                  {selectedProduct.category}
                </span>
                <h2 className="text-xl sm:text-3xl font-extrabold text-neutral-900 mt-3 mb-2">
                  {selectedProduct.name}
                </h2>
                <div className="flex items-center space-x-2 mb-3 sm:mb-4">
                  <span className="text-amber-500 font-bold text-sm">★ {selectedProduct.rating}</span>
                  <span className="text-neutral-400 text-xs sm:text-sm">({selectedProduct.reviewsCount} reviews)</span>
                </div>
                <p className="text-2xl sm:text-3xl font-black text-neutral-900 mb-4 sm:mb-6">
                  ${selectedProduct.price}
                </p>
                <p className="text-xs sm:text-sm text-neutral-600 mb-6 leading-relaxed">
                  {selectedProduct.description}
                </p>

                <div className="mb-6">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-neutral-500 mb-3">Key Specifications</h4>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                    {selectedProduct.specs.map((spec, i) => (
                      <div key={i} className="bg-neutral-50 border border-neutral-200 text-neutral-800 text-xs font-medium px-3 py-2.5 rounded-xl">
                        • {spec}
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              <button
                onClick={() => {
                  addToCart(selectedProduct);
                  setSelectedProduct(null);
                }}
                className="w-full bg-neutral-900 hover:bg-neutral-800 text-white py-3.5 sm:py-4 rounded-full font-bold text-sm transition-all shadow-lg mt-4"
              >
                Add to Cart — ${selectedProduct.price}
              </button>
            </div>
          </div>
        </div>
      )}

      {isCartOpen && (
        <div className="fixed inset-0 z-50 bg-black/65 backdrop-blur-sm flex justify-end animate-fade-in">
          <div className="bg-white w-full max-w-md h-full flex flex-col shadow-2xl relative">
            <div className="p-5 sm:p-6 border-b border-neutral-200 flex items-center justify-between">
              <h2 className="text-lg sm:text-xl font-extrabold text-neutral-900">
                {checkoutStep === 'cart' && `Your Cart (${cart.reduce((s, i) => s + i.quantity, 0)})`}
                {checkoutStep === 'shipping' && 'Shipping Information'}
                {checkoutStep === 'success' && 'Order Confirmed'}
              </h2>
              <button
                onClick={() => setIsCartOpen(false)}
                className="w-9 h-9 bg-neutral-100 hover:bg-neutral-200 rounded-full flex items-center justify-center text-neutral-800 transition-all font-bold"
              >
                ✕
              </button>
            </div>

            <div className="flex-grow overflow-y-auto p-5 sm:p-6">
              {checkoutStep === 'cart' && (
                <>
                  {cart.length === 0 ? (
                    <div className="text-center py-16">
                      <div className="w-16 h-16 bg-neutral-100 rounded-full flex items-center justify-center mx-auto mb-4 text-neutral-400">
                        🛍️
                      </div>
                      <p className="font-medium text-neutral-800 mb-1">Your cart is empty</p>
                      <p className="text-sm text-neutral-500 mb-6">Discover our collection and add your favorite tech.</p>
                      <button
                        onClick={() => setIsCartOpen(false)}
                        className="bg-neutral-900 text-white px-6 py-2.5 rounded-full text-sm font-semibold"
                      >
                        Start Shopping
                      </button>
                    </div>
                  ) : (
                    <div className="space-y-4">
                      {cart.map(item => (
                        <div key={item.id} className="flex items-center space-x-3 sm:space-x-4 bg-neutral-50 p-3.5 sm:p-4 rounded-2xl border border-neutral-200">
                          <img src={item.image} alt={item.name} className="w-14 h-14 sm:w-16 sm:h-16 object-cover rounded-xl bg-white flex-shrink-0" />
                          <div className="flex-grow min-w-0">
                            <h4 className="font-bold text-xs sm:text-sm text-neutral-900 truncate">{item.name}</h4>
                            <p className="text-[11px] sm:text-xs text-neutral-500 mt-0.5">${item.price} each</p>
                            <div className="flex items-center space-x-3 mt-2">
                              <button
                                onClick={() => updateQuantity(item.id, -1)}
                                className="w-6 h-6 bg-white border border-neutral-300 rounded-full flex items-center justify-center text-xs font-bold text-neutral-700 hover:bg-neutral-100"
                              >
                                -
                              </button>
                              <span className="text-xs font-bold text-neutral-900">{item.quantity}</span>
                              <button
                                onClick={() => updateQuantity(item.id, 1)}
                                className="w-6 h-6 bg-white border border-neutral-300 rounded-full flex items-center justify-center text-xs font-bold text-neutral-700 hover:bg-neutral-100"
                              >
                                +
                              </button>
                            </div>
                          </div>
                          <span className="font-extrabold text-xs sm:text-sm text-neutral-900 flex-shrink-0">
                            ${item.price * item.quantity}
                          </span>
                        </div>
                      ))}

                      <form onSubmit={applyPromo} className="flex space-x-2 pt-4">
                        <input
                          type="text"
                          placeholder="Promo Code (VERVE10)"
                          value={promoCode}
                          onChange={e => setPromoCode(e.target.value)}
                          className="flex-grow bg-neutral-100 border border-neutral-200 text-xs px-4 py-3 rounded-xl focus:outline-none focus:ring-2 focus:ring-neutral-900 text-neutral-900"
                        />
                        <button
                          type="submit"
                          className="bg-neutral-200 hover:bg-neutral-300 text-neutral-900 text-xs font-semibold px-4 py-3 rounded-xl transition-all"
                        >
                          Apply
                        </button>
                      </form>
                    </div>
                  )}
                </>
              )}

              {checkoutStep === 'shipping' && (
                <form id="shipping-form" onSubmit={handleCheckoutSubmit} className="space-y-4">
                  <div>
                    <label className="block text-xs font-bold uppercase tracking-wider text-neutral-600 mb-1">Full Name</label>
                    <input
                      type="text"
                      required
                      placeholder="Alex Morgan"
                      value={shippingInfo.name}
                      onChange={e => setShippingInfo({ ...shippingInfo, name: e.target.value })}
                      className="w-full bg-neutral-50 border border-neutral-300 text-sm px-4 py-3 rounded-xl focus:outline-none focus:ring-2 focus:ring-neutral-900 text-neutral-900"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-bold uppercase tracking-wider text-neutral-600 mb-1">Email Address</label>
                    <input
                      type="email"
                      required
                      placeholder="alex@vervetech.com"
                      value={shippingInfo.email}
                      onChange={e => setShippingInfo({ ...shippingInfo, email: e.target.value })}
                      className="w-full bg-neutral-50 border border-neutral-300 text-sm px-4 py-3 rounded-xl focus:outline-none focus:ring-2 focus:ring-neutral-900 text-neutral-900"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-bold uppercase tracking-wider text-neutral-600 mb-1">Shipping Address</label>
                    <input
                      type="text"
                      required
                      placeholder="123 Tech Lane, Suite 400"
                      value={shippingInfo.address}
                      onChange={e => setShippingInfo({ ...shippingInfo, address: e.target.value })}
                      className="w-full bg-neutral-50 border border-neutral-300 text-sm px-4 py-3 rounded-xl focus:outline-none focus:ring-2 focus:ring-neutral-900 text-neutral-900"
                    />
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-xs font-bold uppercase tracking-wider text-neutral-600 mb-1">City</label>
                      <input
                        type="text"
                        required
                        placeholder="San Francisco"
                        value={shippingInfo.city}
                        onChange={e => setShippingInfo({ ...shippingInfo, city: e.target.value })}
                        className="w-full bg-neutral-50 border border-neutral-300 text-sm px-4 py-3 rounded-xl focus:outline-none focus:ring-2 focus:ring-neutral-900 text-neutral-900"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-bold uppercase tracking-wider text-neutral-600 mb-1">Country</label>
                      <input
                        type="text"
                        required
                        placeholder="United States"
                        value={shippingInfo.country}
                        onChange={e => setShippingInfo({ ...shippingInfo, country: e.target.value })}
                        className="w-full bg-neutral-50 border border-neutral-300 text-sm px-4 py-3 rounded-xl focus:outline-none focus:ring-2 focus:ring-neutral-900 text-neutral-900"
                      />
                    </div>
                  </div>
                </form>
              )}

              {checkoutStep === 'success' && (
                <div className="text-center py-12">
                  <div className="w-20 h-20 bg-neutral-900 text-white rounded-full flex items-center justify-center mx-auto mb-6 text-3xl shadow-lg">
                    ✓
                  </div>
                  <h3 className="text-xl sm:text-2xl font-black text-neutral-900 mb-2">Order Placed Successfully!</h3>
                  <p className="text-xs sm:text-sm text-neutral-600 mb-6">
                    Thank you for your order, <span className="font-bold text-neutral-900">{shippingInfo.name}</span>. We have sent a confirmation email to <span className="font-bold text-neutral-900">{shippingInfo.email}</span>.
                  </p>
                  <div className="bg-neutral-50 p-4 rounded-2xl border border-neutral-200 text-xs text-neutral-600 space-y-1 mb-8 text-left">
                    <p><span className="font-bold">Order ID:</span> #VT-784920</p>
                    <p><span className="font-bold">Estimated Delivery:</span> 2-3 Business Days</p>
                    <p><span className="font-bold">Destination:</span> {shippingInfo.address}, {shippingInfo.city}</p>
                  </div>
                  <button
                    onClick={() => { setIsCartOpen(false); setCheckoutStep('cart'); }}
                    className="bg-neutral-900 text-white px-8 py-3.5 rounded-full text-sm font-semibold"
                  >
                    Continue Shopping
                  </button>
                </div>
              )}
            </div>

            {checkoutStep !== 'success' && cart.length > 0 && (
              <div className="p-5 sm:p-6 border-t border-neutral-200 bg-neutral-50">
                <div className="space-y-2 mb-4 text-xs sm:text-sm">
                  <div className="flex justify-between text-neutral-600">
                    <span>Subtotal</span>
                    <span className="font-semibold text-neutral-900">${subtotal}</span>
                  </div>
                  {discount > 0 && (
                    <div className="flex justify-between text-emerald-600 font-medium">
                      <span>Discount (VERVE10)</span>
                      <span>-${discount}</span>
                    </div>
                  )}
                  <div className="flex justify-between text-neutral-600">
                    <span>Shipping</span>
                    <span className="font-semibold text-neutral-900">
                      {shippingFee === 0 ? 'FREE' : `$${shippingFee}`}
                    </span>
                  </div>
                  <div className="flex justify-between text-base sm:text-lg font-black text-neutral-900 pt-2 border-t border-neutral-200">
                    <span>Total</span>
                    <span>${total}</span>
                  </div>
                </div>

                {checkoutStep === 'cart' ? (
                  <button
                    onClick={() => setCheckoutStep('shipping')}
                    className="w-full bg-neutral-900 hover:bg-neutral-800 text-white py-3.5 sm:py-4 rounded-full font-bold text-sm transition-all shadow-lg"
                  >
                    Proceed to Checkout (${total})
                  </button>
                ) : (
                  <div className="flex space-x-3">
                    <button
                      onClick={() => setCheckoutStep('cart')}
                      className="w-1/3 border border-neutral-300 hover:border-neutral-900 text-neutral-900 py-3.5 sm:py-4 rounded-full font-bold text-xs sm:text-sm transition-all bg-white"
                    >
                      Back
                    </button>
                    <button
                      type="submit"
                      form="shipping-form"
                      className="w-2/3 bg-neutral-900 hover:bg-neutral-800 text-white py-3.5 sm:py-4 rounded-full font-bold text-xs sm:text-sm transition-all shadow-lg"
                    >
                      Place Order (${total})
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      <footer className="bg-neutral-900 text-white py-12 sm:py-16 border-t border-neutral-800 mt-auto">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8 sm:gap-10 mb-12">
            <div>
              <span className="text-2xl font-black tracking-tighter uppercase">Verve<span className="text-neutral-400">Tech</span></span>
              <p className="text-xs sm:text-sm text-neutral-400 mt-4 leading-relaxed">
                Effortless tech for the modern lifestyle. Premium engineering, minimalist design, and unmatched reliability.
              </p>
            </div>
            <div>
              <h4 className="text-xs font-bold uppercase tracking-widest text-neutral-400 mb-4">Collection</h4>
              <ul className="space-y-2 text-xs sm:text-sm text-neutral-300">
                <li><button onClick={() => { setSelectedCategory("Audio"); window.scrollTo({ top: 500, behavior: 'smooth' }); }} className="hover:text-white transition-colors">Audio & Sound</button></li>
                <li><button onClick={() => { setSelectedCategory("Wearables"); window.scrollTo({ top: 500, behavior: 'smooth' }); }} className="hover:text-white transition-colors">Smart Wearables</button></li>
                <li><button onClick={() => { setSelectedCategory("Computers"); window.scrollTo({ top: 500, behavior: 'smooth' }); }} className="hover:text-white transition-colors">Computers & Laptops</button></li>
                <li><button onClick={() => { setSelectedCategory("Displays"); window.scrollTo({ top: 500, behavior: 'smooth' }); }} className="hover:text-white transition-colors">OLED Displays</button></li>
              </ul>
            </div>
            <div>
              <h4 className="text-xs font-bold uppercase tracking-widest text-neutral-400 mb-4">Support</h4>
              <ul className="space-y-2 text-xs sm:text-sm text-neutral-300">
                <li><button onClick={() => showToast("Contact support: support@vervetech.com")} className="hover:text-white transition-colors text-left">Contact Us</button></li>
                <li><button onClick={() => showToast("Warranty: 2-Year Global Coverage")} className="hover:text-white transition-colors text-left">Warranty & Repairs</button></li>
                <li><button onClick={() => showToast("Shipping info: Free express worldwide delivery")} className="hover:text-white transition-colors text-left">Shipping & Returns</button></li>
                <li><button onClick={() => showToast("FAQ: Check our knowledge base")} className="hover:text-white transition-colors text-left">FAQ</button></li>
              </ul>
            </div>
            <div>
              <h4 className="text-xs font-bold uppercase tracking-widest text-neutral-400 mb-4">Newsletter</h4>
              <p className="text-xs sm:text-sm text-neutral-400 mb-4">Subscribe to receive early access to new drops and exclusive member pricing.</p>
              <form onSubmit={(e) => { e.preventDefault(); showToast("Successfully subscribed to VerveTech drops!"); }} className="flex space-x-2">
                <input
                  type="email"
                  required
                  placeholder="Enter your email"
                  className="bg-neutral-800 text-white text-xs px-4 py-3 rounded-xl focus:outline-none focus:ring-2 focus:ring-white flex-grow min-w-0"
                />
                <button
                  type="submit"
                  className="bg-white text-neutral-900 text-xs font-bold px-4 py-3 rounded-xl hover:bg-neutral-200 transition-all flex-shrink-0"
                >
                  Join
                </button>
              </form>
            </div>
          </div>
          <div className="pt-8 border-t border-neutral-800 flex flex-col sm:flex-row items-center justify-between text-xs text-neutral-500 space-y-4 sm:space-y-0">
            <p>© 2025 VerveTech Inc. All rights reserved.</p>
            <div className="flex space-x-6">
              <button onClick={() => showToast("Privacy Policy: We protect your data.")} className="hover:text-neutral-300">Privacy Policy</button>
              <button onClick={() => showToast("Terms of Service: Standard retail terms apply.")} className="hover:text-neutral-300">Terms of Service</button>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
