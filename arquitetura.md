# módulos

## main
- `get_db` - API principal para exportação dos dados

## reading

- **Base Anatel** 
  `read_base`
    - `read_mosaico`
    - `read_stel`
    - `read_radcom`
    
- Base Aeronáutica
  `read_aero` 
    - `read_icao`
    - `read_aisw`
    - `read_aisg`

## updates
- **Base Anatel**
 `update_base`
    - `update_mosaico`
    - `update_stel`
    - `update_radcom`
- Base Aeronáutica: `NotImplemented`
- Funções Auxiliares

## merging
- `merge_aero`
- Diversas funções de auxiliares de `merge_aero`

## constants

- Links
    - Spectrum-E Público ( Mosaico )
- Listas
- Dicionários
- SQL Queries `ANATELBDRO05`

## format
- Funções auxiliares de uso interno de tipagem e formatação de DataFrames



