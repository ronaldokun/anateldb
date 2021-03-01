IF OBJECT_ID('tempDB..##faixas','U') is not null 
drop table ##faixas 
create table ##faixas (id int not null, faixa varchar(20), inic float, fim float,); 
insert into ##faixas values(0,'De 20 MHz - 6 GHz','20000', '6000000'); 

select distinct 
f.MedTransmissaoInicial as 'Frequência',
uf.SiglaUnidadeFrequencia as 'Unidade',
e.MedLatitudeDecimal as 'Latitude',
e.MedLongitudeDecimal as 'Longitude',
e.NumServico as 'Número do Serviço',
e.NumEstacao as 'Número da estação',
ent.NomeEntidade as 'Entidade',
mu.NomeMunicipio as 'Município', 
e.SiglaUf as 'UF',
ent.NumCnpjCpf as 'CNPJ',
h.NumFistel as 'Fistel'
from contrato c
inner join estacao e on e.IdtContrato = c.Idtcontrato
inner join frequencia f on f.IdtEstacao = e.IdtEstacao
inner join HABILITACAO h on h.IdtHabilitacao = c.IdtHabilitacao 
inner join entidade ent on ent.IdtEntidade = h.IdtEntidade 
inner join endereco en on en.IdtEstacao = e.IdtEstacao 
inner join Municipio mu on mu.CodMunicipio = en.CodMunicipio 
inner join Servico s on s.NumServico = h.NumServico and s.IdtServicoAreaAtendimento = 4
left join UnidadeFrequencia uf on uf.IdtUnidadeFrequencia = f.IdtUnidadeTransmissao
left outer join ##faixas fx on (
	(fx.inic <= f.MedRecepcaoInicialKHz and fx.fim >= f.MedRecepcaoInicialKHz) 
	or (fx.inic <= f.MedTransmissaoInicialKHz and fx.fim >= f.medtransmissaoinicialkhz)
	or (fx.inic <= f.MedFrequenciaInicialKHz and fx.fim >= f.MedFrequenciaInicialKHz)
	or (fx.inic <= f.MedFrequenciaFinalKHz and fx.fim >= f.MedFrequenciaFinalKHz)
	) 
where e.DataExclusao is null and 
fx.faixa is not null and
f.MedTransmissaoInicial is not null
and h.NumServico <> '010'

