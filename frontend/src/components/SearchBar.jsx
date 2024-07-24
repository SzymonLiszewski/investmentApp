import React from 'react';
import { TextField, Box } from '@mui/material';

const SearchBar = () => {
    return (
        <Box display="flex" alignItems="center" p={1} boxShadow={3} borderRadius={20} bgcolor="#444">
            <TextField 
                variant="standard" 
                placeholder="find your stock" 
                InputProps={{ disableUnderline: true }} 
                style={{ color: 'white' }} 
            />
        </Box>
    );
};

export default SearchBar;
