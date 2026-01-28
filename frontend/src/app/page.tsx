"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Label } from "@/components/ui/label";

type Product = {
  product_name?: string;
  price?: string;
  color?: string;
  material?: string;
  size?: string;
  category?: string;
  subcategory?: string;
  brand?: string;
  features?: string[];
  image_url?: string;
};

export default function Home() {
  const [description, setDescription] = useState("");
  const [loading, setLoading] = useState(false);
  const [products, setProducts] = useState<Product[]>([]);
  const [error, setError] = useState("");



  const handleParse = async () => {
    if (!description.trim()) return;
    setLoading(true);
    setError("");

    try {
      const response = await fetch("http://localhost:8000/parse", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ description }),
      });

      if (!response.ok) {
        throw new Error("Failed to parse description");
      }

      const data = await response.json();
      setProducts([data]);
    } catch (err: any) {
      setError(err.message || "Something went wrong");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="container mx-auto p-4 max-w-6xl">
      <h1 className="text-3xl font-bold mb-6 text-center">AI Product Parser</h1>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="space-y-8">
          <Card>
            <CardHeader>
              <CardTitle>Input Description</CardTitle>
              <CardDescription>Paste a product description below to extract details.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid w-full gap-1.5">
                <Label htmlFor="description">Description</Label>
                <Textarea
                  id="description"
                  placeholder="E.g., Elegant red silk dress, size M, price $120. Perfect for evening wear."
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  rows={5}
                />
              </div>
              {error && <p className="text-red-500 text-sm">{error}</p>}
            </CardContent>
            <CardFooter>
              <Button onClick={handleParse} disabled={loading} className="w-full">
                {loading ? "Parsing..." : "Extract Details"}
              </Button>
            </CardFooter>
          </Card>

          {products.map((product, index) => (
            <Card key={index} className="overflow-hidden border-2 hover:border-primary/50 transition-colors">
              <CardHeader className="bg-muted/50 pb-4">
                <div className="flex justify-between items-start">
                   <div>
                      <CardTitle className="text-xl">{product.product_name || "Unknown Product"}</CardTitle>
                      <CardDescription>{product.brand || "Unknown Brand"}</CardDescription>
                   </div>
                   {product.category && <Badge variant="secondary">{product.category}</Badge>}
                </div>
              </CardHeader>
              <CardContent className="pt-6 space-y-4">
                 {product.image_url && (
                    <div className="mb-4 aspect-video relative overflow-hidden rounded-md border bg-muted">
                      {/* eslint-disable-next-line @next/next/no-img-element */}
                      <img 
                        src={product.image_url} 
                        alt={product.product_name}
                        className="object-cover w-full h-full" 
                        onError={(e) => {
                          (e.target as HTMLImageElement).style.display = 'none';
                        }}
                      />
                    </div>
                 )}
                 <div className="flex items-center justify-between">
                    <span className="text-2xl font-bold text-green-600">{product.price || "N/A"}</span>
                    {product.color && (
                      <div className="flex items-center gap-2" title={`Color: ${product.color}`}>
                        <div 
                          className="w-6 h-6 rounded-full border shadow-sm"
                          style={{ backgroundColor: product.color }}
                        />
                        <span className="text-sm text-muted-foreground capitalize">{product.color}</span>
                      </div>
                    )}
                 </div>
                 
                 <div className="grid grid-cols-2 gap-2 text-sm">
                    <div className="flex flex-col">
                      <span className="font-medium text-muted-foreground">Material</span>
                      <span>{product.material || "Not specified"}</span>
                    </div>
                    <div className="flex flex-col">
                      <span className="font-medium text-muted-foreground">Size</span>
                      <span>{product.size || "Not specified"}</span>
                    </div>
                     <div className="flex flex-col">
                      <span className="font-medium text-muted-foreground">Subcategory</span>
                      <span>{product.subcategory || "N/A"}</span>
                    </div>
                 </div>
                 
                 {product.features && product.features.length > 0 && (
                   <div className="mt-4">
                      <span className="font-medium text-muted-foreground block mb-2">Features</span>
                      <div className="flex flex-wrap gap-2">
                        {product.features.map((feature, i) => (
                          <Badge key={i} variant="outline" className="text-xs">{feature}</Badge>
                        ))}
                      </div>
                   </div>
                 )}
              </CardContent>
            </Card>
          ))}
        </div>

        <div>
          {products.length > 0 && (
            <Card className="h-full max-h-[800px] flex flex-col">
              <CardHeader>
                <CardTitle>JSON Output</CardTitle>
                <CardDescription>Raw extraction result from the API.</CardDescription>
              </CardHeader>
              <CardContent className="flex-1 overflow-auto">
                <pre className="text-xs bg-muted p-4 rounded-lg overflow-x-auto whitespace-pre-wrap font-mono h-full">
                  {JSON.stringify(products[0], null, 2)}
                </pre>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </main>
  );
}
