import React, { useState } from 'react';
import {
  Card,
  CardContent,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  Typography,
  Chip,
  TextField,
  Stack,
} from '@mui/material';
import SearchIcon from '@mui/icons-material/Search';
import type { DetectionResult } from '../types/detection';

interface FODTableProps {
  detections: DetectionResult[];
}

export const FODTable: React.FC<FODTableProps> = ({ detections }) => {
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [searchTerm, setSearchTerm] = useState('');

  const handleChangePage = (_: unknown, newPage: number) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  const filteredDetections = detections.filter((detection) =>
    detection.id.toLowerCase().includes(searchTerm.toLowerCase()) ||
    detection.timestamp.includes(searchTerm)
  );

  const paginatedDetections = filteredDetections.slice(
    page * rowsPerPage,
    page * rowsPerPage + rowsPerPage
  );

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.9) return 'success';
    if (confidence >= 0.8) return 'warning';
    return 'error';
  };

  if (detections.length === 0) {
    return (
      <Card
        sx={{
          backgroundColor: 'background.paper',
          border: '1px solid',
          borderColor: 'divider',
        }}
      >
        <CardContent sx={{ textAlign: 'center', py: 4 }}>
          <Typography color="textSecondary">
            No FOD detections to display
          </Typography>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card
      sx={{
        backgroundColor: 'background.paper',
        border: '1px solid',
        borderColor: 'divider',
      }}
    >
      <CardContent>
        <Stack spacing={2} sx={{ mb: 2 }}>
          <Typography variant="h6">FOD Detection Details</Typography>
          <TextField
            placeholder="Search by FOD ID or timestamp..."
            size="small"
            value={searchTerm}
            onChange={(e) => {
              setSearchTerm(e.target.value);
              setPage(0);
            }}
            slotProps={{
              input: {
                startAdornment: <SearchIcon sx={{ mr: 1, color: 'textSecondary' }} />,
              },
            }}
            sx={{
              maxWidth: 400,
              '& .MuiOutlinedInput-root': {
                borderRadius: 1,
              },
            }}
          />
        </Stack>

        <TableContainer sx={{ maxHeight: 600, overflowY: 'auto' }}>
          <Table stickyHeader>
            <TableHead>
              <TableRow sx={{ backgroundColor: '#0a0e27' }}>
                <TableCell sx={{ fontWeight: 'bold', color: 'primary.main' }}>
                  FOD ID
                </TableCell>
                <TableCell align="center" sx={{ fontWeight: 'bold', color: 'primary.main' }}>
                  Frame
                </TableCell>
                <TableCell sx={{ fontWeight: 'bold', color: 'primary.main' }}>
                  Timestamp
                </TableCell>
                <TableCell align="right" sx={{ fontWeight: 'bold', color: 'primary.main' }}>
                  Distance (m)
                </TableCell>
                <TableCell align="right" sx={{ fontWeight: 'bold', color: 'primary.main' }}>
                  X Coord
                </TableCell>
                <TableCell align="right" sx={{ fontWeight: 'bold', color: 'primary.main' }}>
                  Y Coord
                </TableCell>
                <TableCell align="center" sx={{ fontWeight: 'bold', color: 'primary.main' }}>
                  Confidence
                </TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {paginatedDetections.map((detection, index) => (
                <TableRow
                  key={detection.id}
                  sx={{
                    backgroundColor: index % 2 === 0 ? 'transparent' : 'rgba(0, 188, 212, 0.05)',
                    '&:hover': {
                      backgroundColor: 'rgba(0, 188, 212, 0.1)',
                    },
                  }}
                >
                  <TableCell>
                    <Chip
                      label={detection.id}
                      color="primary"
                      variant="outlined"
                      size="small"
                    />
                  </TableCell>
                  <TableCell align="center">
                    {detection.frame}
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2">{detection.timestamp}</Typography>
                  </TableCell>
                  <TableCell align="right">
                    <Typography variant="body2" sx={{ color: 'warning.main', fontWeight: 'bold' }}>
                      {detection.distance_m.toFixed(1)}
                    </Typography>
                  </TableCell>
                  <TableCell align="right">
                    <Typography variant="body2">{detection.coordinates.x.toFixed(2)}</Typography>
                  </TableCell>
                  <TableCell align="right">
                    <Typography variant="body2">{detection.coordinates.y.toFixed(2)}</Typography>
                  </TableCell>
                  <TableCell align="center">
                    <Chip
                      label={`${(detection.confidence * 100).toFixed(1)}%`}
                      color={getConfidenceColor(detection.confidence) as any}
                      size="small"
                      variant="filled"
                    />
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>

        <TablePagination
          rowsPerPageOptions={[5, 10, 25, 50]}
          component="div"
          count={filteredDetections.length}
          rowsPerPage={rowsPerPage}
          page={page}
          onPageChange={handleChangePage}
          onRowsPerPageChange={handleChangeRowsPerPage}
          sx={{
            '& .MuiTablePagination-selectLabel, & .MuiTablePagination-displayedRows': {
              margin: 0,
            },
          }}
        />
      </CardContent>
    </Card>
  );
};
