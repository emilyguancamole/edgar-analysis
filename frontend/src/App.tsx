import { useState } from 'react'
import { Container, Typography } from "@mui/material";
import './App.css'

import HoldingsTable from './components/HoldingsTable'

function App() {

  return (
    <Container>
      <Typography sx={{ mt: 4 }} variant="h1" align="center" gutterBottom>
        EDGAR
      </Typography>
      <HoldingsTable cik="CIK0000763212" />
    </Container>
  )
}

export default App
