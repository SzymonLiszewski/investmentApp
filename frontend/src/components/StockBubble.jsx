import React from 'react';
import { Box, Avatar, Typography } from '@mui/material';

const StockBubble = ({ logo, symbol }) => {
    return (
        <Box 
            display="flex" 
            alignItems="center" 
            justifyContent="center"
            borderRadius="50px"
            boxShadow={3}
            p={1}
            m={1}
            bgcolor="#ffffff"
            sx={{
                '&:hover': {
            bgcolor: '#b8b8b8',
          }
            }}
        >
            <Avatar src={logo} alt={symbol} style={{ marginRight: 8 }} />
            <Typography variant="h6" color="black">{symbol}</Typography>
        </Box>
    );
};

export default StockBubble;
