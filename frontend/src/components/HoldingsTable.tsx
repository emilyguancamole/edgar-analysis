import { DataGrid, type GridColDef } from "@mui/x-data-grid";

import { useCallback, useEffect, useState } from "react";
import { fetchHoldingsRow } from "../data/api";
import type { HoldingsRowType } from "../data/types";

type HoldingsTableProps = {
    cik: string;
    pageSizeDefault?: number;
}

const HoldingsTable = ({ cik, pageSizeDefault=50 }: HoldingsTableProps) => {
    const [rows, setRows] = useState<HoldingsRowType[]>([]);
    const [page, setPage] = useState(0); // DataGrid page is 0-based
    // Server-side pagination requires the API to return total count and page rows
    const [pageSize, setPageSize] = useState<number>(pageSizeDefault);
    const [rowCount, setRowCount] = useState<number>(0);
    const [loading, setLoading] = useState<boolean>(false);

    const loadPage = useCallback(async (page: number, pageSize: number) => { // Memoized function, re-created only when cik changes
        setLoading(true);
        try {
            // API expects 1-based page index
            const data = await fetchHoldingsRow(cik, page + 1, pageSize);
            console.log("Fetched data:", data);
            setRows(data.rows ?? []);
            setRowCount(typeof data.total === "number" ? data.total : (data.rows?.length ?? 0));
        } finally {
            setLoading(false);
        }
    }, [cik]);

    useEffect(() => {
        loadPage(page, pageSize);
    }, [page, pageSize, cik, loadPage]);

  const columns: GridColDef[] = [
    { field: "issuer_name", headerName: "Security", width: 220 },
    { field: "date", headerName: "Date", width: 120 },
    { field: "shares_owned", headerName: "Shares", width: 140, type: "number" },
    {
      field: "shares_change",
      headerName: "Shares Change",
      width: 140,
      type: "number",
    },
    {
      field: "shares_change_pct",
      headerName: "Shares % Change",
      width: 140,
      type: "number",
      valueFormatter: (params: any) => {
        const v = Number(params.value ?? 0);
        return `${(v * 100).toFixed(2)}%`;
      }
    }
  ];

  return (
    <div style={{ height: 600, width: "100%" }}>
    <DataGrid
      {...{
        rows,
        columns,
        pagination: true,
        paginationMode: "server",
        paginationModel: { page, pageSize },
        pageSizeOptions: [25, 50, 100],
        rowCount,
        onPaginationModelChange: (model: any) => {
          if (model.page !== page) setPage(model.page);
          if (model.pageSize !== pageSize) { setPageSize(model.pageSize); setPage(0); }
        },
        getRowId: (row: any) => row.id,
        loading,
      } as any}
    />
    </div>
  );
}

export default HoldingsTable;