import React, { useState, useEffect, useCallback } from 'react';
import { Image, ScrollView, View } from 'react-native';
import { TextInput, Card, Text, Divider, useTheme, Chip, Button } from 'react-native-paper';
import axios from 'axios';
import debounce from 'lodash.debounce';

interface Seller {
  price: number;
  link: string;
  storeId: string;
}

interface Variation {
  weight: number;
  measure: string;
  name: string;
  imageUrl: string;
  sellers: Seller[];
}

interface Product {
  id: string;
  brand: string;
  clusteredName: string;
  variations: Variation[];
}

export default function TabOneScreen() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<Product[]>([]);
  const [cart, setCart] = useState<Seller[]>([]);
  const theme = useTheme();

  const search = async (searchText: string) => {
    if (!searchText.trim()) {
      setResults([]);
      return;
    }

    try {
      const response = await axios.post('http://172.23.80.1:9200/products/_search', {
        query: {
          bool: {
            must: {
              match: {
                clusteredName: searchText
              }
            }
          }
        }
      });

      const hits = response.data.hits.hits;
      const products = hits.map((hit: any) => ({
        id: hit._id,
        ...hit._source
      }));
      setResults(products);
    } catch (error) {
      console.error('Error searching:', error);
    }
  };

  // debounce de 500ms
  const debouncedSearch = useCallback(debounce(search, 500), []);

  const handleQueryChange = (text: string) => {
    setQuery(text);
    debouncedSearch(text);
  };

  const addToCart = (seller: Seller) => {
    setCart(prev => [...prev, seller]);
  };

  return (
    <ScrollView style={{ padding: 20, backgroundColor: '#FAFAFA' }}>
      <TextInput
        label="Buscar produto"
        value={query}
        onChangeText={handleQueryChange}
        mode="outlined"
        style={{ marginBottom: 20 }}
      />

      {results.map(product => (
        <Card key={product.id} style={{ marginBottom: 20, borderRadius: 12, elevation: 2 }}>
          <Card.Title
            title={product.clusteredName}
            subtitle={`Marca: ${product.brand}`}
            titleStyle={{ fontWeight: 'bold' }}
          />
          <Card.Content>
            {product.variations.map((variation, index) => {
              const prices = variation.sellers.map(seller => seller.price);
              const minPrice = Math.min(...prices);
              const maxPrice = Math.max(...prices);
              const priceDisplay =
                minPrice === maxPrice
                  ? `R$${minPrice.toFixed(2)}`
                  : `R$${minPrice.toFixed(2)} - R$${maxPrice.toFixed(2)}`;

              return (
                <View key={index} style={{ marginBottom: 16 }}>
                  <Divider style={{ marginVertical: 8 }} />
                  <View style={{ flexDirection: 'row', gap: 12 }}>
                    {variation.imageUrl && (
                      <Image
                        source={{ uri: variation.imageUrl }}
                        style={{ width: 90, height: 90, borderRadius: 8 }}
                        resizeMode="contain"
                      />
                    )}
                    <View style={{ flex: 1 }}>
                      <Text style={{ fontWeight: '600', fontSize: 16 }}>
                        {variation.name}
                      </Text>
                      <Text style={{ color: theme.colors.secondary }}>
                        {variation.weight} {variation.measure}
                      </Text>
                      <Text style={{ marginTop: 4, fontSize: 15, fontWeight: 'bold' }}>
                        {priceDisplay}
                      </Text>
                      <View style={{ flexDirection: 'row', flexWrap: 'wrap', marginTop: 4 }}>
                        {variation.sellers.map((seller, i) => (
                          <Chip key={i} style={{ marginRight: 6, marginBottom: 4 }}>
                            {seller.storeId}
                          </Chip>
                        ))}
                      </View>
                      <Button
                        mode="contained-tonal"
                        onPress={() => addToCart(variation.sellers[0])}
                        style={{ marginTop: 8 }}
                      >
                        Adicionar ao carrinho
                      </Button>
                    </View>
                  </View>
                </View>
              );
            })}
          </Card.Content>
        </Card>
      ))}

      {cart.length > 0 && (
        <Card style={{ marginTop: 30, borderRadius: 12, backgroundColor: '#FFF' }}>
          <Card.Title title="🛒 Shopping List" />
          <Card.Content>
            {cart.map((item, index) => (
              <Text key={index} style={{ marginBottom: 6 }}>
                • R${item.price.toFixed(2)} - {item.link}
              </Text>
            ))}
          </Card.Content>
        </Card>
      )}
    </ScrollView>
  );
}
