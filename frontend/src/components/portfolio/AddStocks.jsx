import React, { useState, useEffect, useCallback } from 'react';
import { TextField, Button, Container, Typography, Box, MenuItem, Select, FormControl, InputLabel, Autocomplete } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import '../styles/AddStocks.css';
import apiClient from '../../api/client';

const AddStocks = () => {
  const [assetType, setAssetType] = useState('stocks');
  const [symbol, setSymbol] = useState('');
  const [name, setName] = useState('');
  const [count, setCount] = useState('');
  const [type, setType] = useState('B');
  const [_price, setPrice] = useState('');
  const [_date, setDate] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [suggestions, setSuggestions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedAsset, setSelectedAsset] = useState(null);
  
  // Bond-specific state
  const [bondMode, setBondMode] = useState('search'); // 'search' or 'manual'
  const [bondType, setBondType] = useState('');
  const [bondSeries, setBondSeries] = useState('');
  const [maturityDate, setMaturityDate] = useState('');
  const [interestRateType, setInterestRateType] = useState('fixed');
  const [interestRate, setInterestRate] = useState('');
  const [wiborMargin, setWiborMargin] = useState('');
  const [inflationMargin, setInflationMargin] = useState('');
  const [baseInterestRate, setBaseInterestRate] = useState('');
  const [faceValue, setFaceValue] = useState('100');

  const navigate = useNavigate();

  // Debounced search function
  const searchAssets = useCallback(async (query) => {
    if (query.length < 2) {
      setSuggestions([]);
      return;
    }

    setLoading(true);
    try {
      const params = new URLSearchParams({
        q: query,
        asset_type: assetType,
        limit: '20'
      });
      const response = await apiClient.get(`api/assets/search/?${params}`);
      setSuggestions(response.data);
    } catch (error) {
      console.error('Error searching assets:', error);
      setSuggestions([]);
    } finally {
      setLoading(false);
    }
  }, [assetType]);

  // Debounce effect
  useEffect(() => {
    const timer = setTimeout(() => {
      if (searchQuery) {
        searchAssets(searchQuery);
      } else {
        setSuggestions([]);
      }
    }, 300); // 300ms debounce

    return () => clearTimeout(timer);
  }, [searchQuery, searchAssets]);

  // Reset search when asset type changes
  useEffect(() => {
    setSearchQuery('');
    setSuggestions([]);
    setSelectedAsset(null);
    setSymbol('');
    setName('');
    // Reset bond fields
    setBondMode('search');
    setBondType('');
    setBondSeries('');
    setMaturityDate('');
    setInterestRateType('fixed');
    setInterestRate('');
    setWiborMargin('');
    setInflationMargin('');
    setBaseInterestRate('');
    setFaceValue('100');
  }, [assetType]);

  // Handle asset selection from autocomplete
  const handleAssetSelect = (event, value) => {
    if (value) {
      setSelectedAsset(value);
      setSymbol(value.symbol || '');
      setName(value.name || '');
      setSearchQuery(value.symbol || value.name || '');
    } else {
      setSelectedAsset(null);
      setSymbol('');
      setName('');
      setSearchQuery('');
    }
  };

  // Handle manual input change
  const handleSearchInputChange = (event, newValue) => {
    setSearchQuery(newValue || '');
    if (!newValue) {
      setSelectedAsset(null);
      setSymbol('');
      setName('');
    }
  };
    
  const handleSubmit = async (e) => {
    e.preventDefault();
    const result = await addAssetAndTransaction();
    console.log(result);
  };

  const addAssetAndTransaction = async () => {
    try {
      // Prepare transaction data with asset information
      const transactionData = {
        quantity: parseFloat(count),
        transactionType: type,
        price: _price ? parseFloat(_price) : null,
        date: _date || new Date().toISOString().split('T')[0],
        asset_type: assetType,
        name: name
      };

      // Add symbol if provided
      if (assetType === 'stocks' || (assetType === 'bonds' || assetType === 'cryptocurrencies') && symbol) {
        transactionData.symbol = symbol;
      }
      
      // Add bond-specific fields if manual mode
      if (assetType === 'bonds' && bondMode === 'manual') {
        transactionData.bond_type = bondType;
        transactionData.bond_series = bondSeries || null;
        transactionData.maturity_date = maturityDate;
        transactionData.interest_rate_type = interestRateType;
        transactionData.face_value = parseFloat(faceValue) || 100;
        
        if (interestRateType === 'fixed') {
          transactionData.interest_rate = interestRate ? parseFloat(interestRate) : null;
        } else if (interestRateType === 'variable_wibor') {
          transactionData.wibor_margin = wiborMargin ? parseFloat(wiborMargin) : null;
        } else if (interestRateType === 'indexed_inflation') {
          transactionData.inflation_margin = inflationMargin ? parseFloat(inflationMargin) : null;
          transactionData.base_interest_rate = baseInterestRate ? parseFloat(baseInterestRate) : null;
        }
      }

      const response = await apiClient.post('api/portfolio/transactions/', transactionData);
      const data = response.data;

      alert('Asset added successfully');
      navigate('/');
      return data;
    } catch (error) {
      alert('Error: ' + error.message);
    }
  }

  return (
    <div className="add-stocks-container">
      <Container maxWidth="xs" sx={{ width: '100%' }}>
        <Box
          display="flex"
          flexDirection="column"
          justifyContent="center"
          alignItems="center"
          width="100%"
        >
          <Typography variant="h4" component="h1" gutterBottom>
            Add Assets
          </Typography>
          <form onSubmit={handleSubmit} style={{ width: '100%' }}>
          <FormControl fullWidth margin="normal">
            <InputLabel>Asset Type</InputLabel>
            <Select
              value={assetType}
              label="Asset Type"
              onChange={(e) => setAssetType(e.target.value)}
            >
              <MenuItem value="stocks">Stocks</MenuItem>
              <MenuItem value="bonds">Bonds</MenuItem>
              <MenuItem value="cryptocurrencies">Cryptocurrencies</MenuItem>
            </Select>
          </FormControl>

          {assetType === 'stocks' && (
            <>
              <Autocomplete
                freeSolo
                options={suggestions}
                getOptionLabel={(option) => {
                  if (typeof option === 'string') return option;
                  return `${option.symbol} - ${option.name}`;
                }}
                loading={loading}
                value={selectedAsset}
                inputValue={searchQuery}
                onInputChange={handleSearchInputChange}
                onChange={handleAssetSelect}
                renderInput={(params) => (
                  <TextField
                    {...params}
                    label="Search by Symbol or Name *"
                    variant="outlined"
                    margin="normal"
                    required
                    helperText="Start typing to search for stocks"
                  />
                )}
                renderOption={(props, option) => (
                  <Box component="li" {...props} key={option.id}>
                    <Box>
                      <Typography variant="body1" fontWeight="bold">
                        {option.symbol}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {option.name}
                      </Typography>
                    </Box>
                  </Box>
                )}
              />
              <TextField
                label="Symbol *"
                variant="outlined"
                margin="normal"
                fullWidth
                required
                value={symbol}
                onChange={(e) => setSymbol(e.target.value)}
                disabled={!!selectedAsset}
              />
              <TextField
                label="Name *"
                variant="outlined"
                margin="normal"
                fullWidth
                required
                value={name}
                onChange={(e) => setName(e.target.value)}
                disabled={!!selectedAsset}
              />
            </>
          )}

          {assetType === 'bonds' && (
            <>
              <FormControl fullWidth margin="normal">
                <InputLabel>Bond Entry Mode</InputLabel>
                <Select
                  value={bondMode}
                  label="Bond Entry Mode"
                  onChange={(e) => setBondMode(e.target.value)}
                >
                  <MenuItem value="search">Search from Database</MenuItem>
                  <MenuItem value="manual">Enter Manually</MenuItem>
                </Select>
              </FormControl>

              {bondMode === 'search' && (
                <>
                  <Autocomplete
                    freeSolo
                    options={suggestions}
                    getOptionLabel={(option) => {
                      if (typeof option === 'string') return option;
                      return option.symbol ? `${option.symbol} - ${option.name}` : option.name;
                    }}
                    loading={loading}
                    value={selectedAsset}
                    inputValue={searchQuery}
                    onInputChange={handleSearchInputChange}
                    onChange={handleAssetSelect}
                    renderInput={(params) => (
                      <TextField
                        {...params}
                        label="Search by Symbol or Name *"
                        variant="outlined"
                        margin="normal"
                        required
                        helperText="Start typing to search for bonds"
                      />
                    )}
                    renderOption={(props, option) => (
                      <Box component="li" {...props} key={option.id}>
                        <Box>
                          {option.symbol && (
                            <Typography variant="body1" fontWeight="bold">
                              {option.symbol}
                            </Typography>
                          )}
                          <Typography variant="body2" color="text.secondary">
                            {option.name}
                          </Typography>
                        </Box>
                      </Box>
                    )}
                  />
                  <TextField
                    label="Name *"
                    variant="outlined"
                    margin="normal"
                    fullWidth
                    required
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    disabled={!!selectedAsset}
                  />
                  <TextField
                    label="Symbol (optional)"
                    variant="outlined"
                    margin="normal"
                    fullWidth
                    value={symbol}
                    onChange={(e) => setSymbol(e.target.value)}
                    disabled={!!selectedAsset}
                  />
                </>
              )}

              {bondMode === 'manual' && (
                <>
                  <FormControl fullWidth margin="normal">
                    <InputLabel>Bond Type *</InputLabel>
                    <Select
                      value={bondType}
                      label="Bond Type *"
                      onChange={(e) => setBondType(e.target.value)}
                      required
                    >
                      <MenuItem value="OS">OS - Obligacje Skarbowe</MenuItem>
                      <MenuItem value="OTS">OTS - Obligacje Trzymiesięczne</MenuItem>
                      <MenuItem value="EDO">EDO - Emerytalne Obligacje Długoterminowe</MenuItem>
                      <MenuItem value="ROR">ROR - Obligacje Rocznie Oprocentowane</MenuItem>
                      <MenuItem value="DOR">DOR - Obligacje Dwuletnie Oprocentowane Zmiennie</MenuItem>
                      <MenuItem value="TOS">TOS - Obligacje Trzyletnie Oprocentowane Stałe</MenuItem>
                      <MenuItem value="COI">COI - Obligacje Czteroletnie Oprocentowane Indeksowane</MenuItem>
                      <MenuItem value="ROS">ROS - Obligacje Rocznie Oprocentowane Stałe</MenuItem>
                      <MenuItem value="ROD">ROD - Obligacje Rocznie Oprocentowane Dwuletnie</MenuItem>
                    </Select>
                  </FormControl>
                  <TextField
                    label="Bond Series (optional)"
                    variant="outlined"
                    margin="normal"
                    fullWidth
                    value={bondSeries}
                    onChange={(e) => setBondSeries(e.target.value)}
                    helperText="e.g., OS0424"
                  />
                  <TextField
                    label="Name *"
                    variant="outlined"
                    margin="normal"
                    fullWidth
                    required
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                  />
                  <TextField
                    label="Maturity Date *"
                    type="date"
                    variant="outlined"
                    margin="normal"
                    fullWidth
                    required
                    InputLabelProps={{
                      shrink: true,
                    }}
                    value={maturityDate}
                    onChange={(e) => setMaturityDate(e.target.value)}
                  />
                  <FormControl fullWidth margin="normal">
                    <InputLabel>Interest Rate Type *</InputLabel>
                    <Select
                      value={interestRateType}
                      label="Interest Rate Type *"
                      onChange={(e) => setInterestRateType(e.target.value)}
                      required
                    >
                      <MenuItem value="fixed">Fixed</MenuItem>
                      <MenuItem value="variable_wibor">Variable (WIBOR)</MenuItem>
                      <MenuItem value="indexed_inflation">Indexed (Inflation)</MenuItem>
                    </Select>
                  </FormControl>
                  
                  {interestRateType === 'fixed' && (
                    <TextField
                      label="Interest Rate (%) *"
                      type="number"
                      variant="outlined"
                      margin="normal"
                      fullWidth
                      required
                      value={interestRate}
                      onChange={(e) => setInterestRate(e.target.value)}
                      inputProps={{ step: "0.01", min: "0" }}
                    />
                  )}
                  
                  {interestRateType === 'variable_wibor' && (
                    <TextField
                      label="WIBOR Margin (%) *"
                      type="number"
                      variant="outlined"
                      margin="normal"
                      fullWidth
                      required
                      value={wiborMargin}
                      onChange={(e) => setWiborMargin(e.target.value)}
                      inputProps={{ step: "0.01" }}
                      helperText="Margin added to WIBOR rate"
                    />
                  )}
                  
                  {interestRateType === 'indexed_inflation' && (
                    <>
                      <TextField
                        label="Base Interest Rate (%) (First Period)"
                        type="number"
                        variant="outlined"
                        margin="normal"
                        fullWidth
                        value={baseInterestRate}
                        onChange={(e) => setBaseInterestRate(e.target.value)}
                        inputProps={{ step: "0.01", min: "0" }}
                        helperText="Rate for the first period (optional)"
                      />
                      <TextField
                        label="Inflation Margin (%) *"
                        type="number"
                        variant="outlined"
                        margin="normal"
                        fullWidth
                        required
                        value={inflationMargin}
                        onChange={(e) => setInflationMargin(e.target.value)}
                        inputProps={{ step: "0.01" }}
                        helperText="Margin added to inflation rate"
                      />
                    </>
                  )}
                  
                  <TextField
                    label="Face Value (PLN)"
                    type="number"
                    variant="outlined"
                    margin="normal"
                    fullWidth
                    value={faceValue}
                    onChange={(e) => setFaceValue(e.target.value)}
                    inputProps={{ step: "0.01", min: "0" }}
                    helperText="Default: 100 PLN"
                  />
                </>
              )}
            </>
          )}

          {assetType === 'cryptocurrencies' && (
            <>
              <Autocomplete
                freeSolo
                options={suggestions}
                getOptionLabel={(option) => {
                  if (typeof option === 'string') return option;
                  return option.symbol ? `${option.symbol} - ${option.name}` : option.name;
                }}
                loading={loading}
                value={selectedAsset}
                inputValue={searchQuery}
                onInputChange={handleSearchInputChange}
                onChange={handleAssetSelect}
                renderInput={(params) => (
                  <TextField
                    {...params}
                    label="Search by Symbol or Name *"
                    variant="outlined"
                    margin="normal"
                    required
                    helperText="Start typing to search for cryptocurrencies. Use pair format (e.g. BTC-USD, ETH-USD) for valuation."
                  />
                )}
                renderOption={(props, option) => (
                  <Box component="li" {...props} key={option.id}>
                    <Box>
                      {option.symbol && (
                        <Typography variant="body1" fontWeight="bold">
                          {option.symbol}
                        </Typography>
                      )}
                      <Typography variant="body2" color="text.secondary">
                        {option.name}
                      </Typography>
                    </Box>
                  </Box>
                )}
              />
              <TextField
                label="Name *"
                variant="outlined"
                margin="normal"
                fullWidth
                required
                value={name}
                onChange={(e) => setName(e.target.value)}
                disabled={!!selectedAsset}
              />
              <TextField
                label="Symbol *"
                variant="outlined"
                margin="normal"
                fullWidth
                required
                value={symbol}
                onChange={(e) => setSymbol(e.target.value)}
                disabled={!!selectedAsset}
                helperText="Use pair format, e.g. BTC-USD, ETH-USD (required for valuation)"
              />
            </>
          )}

          <TextField
            label="Quantity *"
            type="number"
            variant="outlined"
            margin="normal"
            fullWidth
            required
            value={count}
            onChange={(e) => setCount(e.target.value)}
          />
          <FormControl fullWidth margin="normal">
            <InputLabel>Transaction Type</InputLabel>
            <Select
              value={type}
              label="Transaction Type"
              onChange={(e) => setType(e.target.value)}
            >
              <MenuItem value="B">Buy</MenuItem>
              <MenuItem value="S">Sell</MenuItem>
            </Select>
          </FormControl>
          <TextField
            label="Price"
            type="number"
            variant="outlined"
            margin="normal"
            fullWidth
            value={_price}
            onChange={(e) => setPrice(e.target.value)}
            helperText="Leave empty to use the closing price for the selected date"
            inputProps={{ step: '0.01', min: '0' }}
          />
          <TextField
            label="Date"
            type="date"
            variant="outlined"
            margin="normal"
            fullWidth
            InputLabelProps={{
              shrink: true,
            }}
            value={_date}
            onChange={(e) => setDate(e.target.value)}
          />
          <Button
            type="submit"
            variant="contained"
            color="primary"
            fullWidth
            style={{ marginTop: '16px' }}
          >
            Add Assets
          </Button>
          </form>
        </Box>
      </Container>
    </div>
  );
};

export default AddStocks;