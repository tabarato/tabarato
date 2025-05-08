import React, { useState, useEffect, useCallback } from 'react';
import { Image, ScrollView, View } from 'react-native';
import { TextInput, Card, Text, Divider, useTheme, Chip, Button } from 'react-native-paper';
import axios from 'axios';
import debounce from 'lodash.debounce';

interface Variation {
  weight: number;
  measure: string;
  name: string;
  image_url: string;
  min_price: number;
  max_price: number;
  stores: string[];
}

interface Product {
  id: string;
  brand: string;
  name: string;
  variations: Variation[];
}

export default function TabOneScreen() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<Product[]>([]);
  const [cart, setCart] = useState<Variation[]>([]);
  const [showStores, setShowStores] = useState(false);
  const [secretCount, setSecretCount] = useState(0);

  const handleSecretTap = () => {
    setSecretCount(prev => {
      const next = prev + 1;
      if (next >= 5) {
        setShowStores(true);
      }
      return next;
    });
  };

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
              multi_match: {
                query: searchText,
                type: "most_fields",
                fields: [
                  "name^3",
                  "brand"
                ]
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

  const addToCart = (variation: Variation) => {
    setCart(prev => [...prev, variation]);
  };

  return (
    <ScrollView style={{ padding: 20, backgroundColor: '#FAFAFA' }}>
      <Text
        onPress={handleSecretTap}
        style={{ textAlign: 'center', marginBottom: 10, color: '#999' }}
      >
        🛠️ Dev Mode
      </Text>
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
            title={product.name}
            subtitle={`Marca: ${product.brand}`}
            titleStyle={{ fontWeight: 'bold' }}
          />
          <Card.Content>
            {product.variations.map((variation, index) => {
              const priceDisplay =
                variation.min_price === variation.max_price
                  ? `R$${variation.min_price.toFixed(2)}`
                  : `R$${variation.min_price.toFixed(2)} - R$${variation.max_price.toFixed(2)}`;

              return (
                <View key={index} style={{ marginBottom: 16 }}>
                  <Divider style={{ marginVertical: 8 }} />
                  <View style={{ flexDirection: 'row', gap: 12 }}>
                    {variation.image_url && (
                      <Image
                        source={{ uri: variation.image_url }}
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
                      {showStores && (
                        <ScrollView horizontal showsHorizontalScrollIndicator={false} style={{ marginTop: 12 }}>
                          {variation.stores.map((store, idx) => (
                            <Card
                              key={idx}
                              style={{
                                marginRight: 12,
                                paddingVertical: 6,
                                paddingHorizontal: 12,
                                backgroundColor: '#F0F4FF',
                                borderRadius: 10,
                                minWidth: 100,
                                justifyContent: 'center',
                              }}
                            >
                              <Card.Content style={{ flexDirection: 'row', alignItems: 'center', gap: 6 }}>
                                <Text style={{ fontWeight: '600', fontSize: 14, color: '#3B4CCA' }}>🏬 {store}</Text>
                              </Card.Content>
                            </Card>
                          ))}
                        </ScrollView>
                      )}
                      <Button
                        mode="contained-tonal"
                        onPress={() => addToCart(variation)}
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
                • R${item.min_price.toFixed(2)}
              </Text>
            ))}
          </Card.Content>
        </Card>
      )}
    </ScrollView>
  );
}
