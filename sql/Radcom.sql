use SITARWEB

select f.MedFrequenciaInicial as 'Frequência', 
       uf.SiglaUnidadeFrequencia as 'Unidade',
       es.MedLatitudeDecimal as 'Latitude' ,
	   es.MedLongitudeDecimal as 'Longitude',
       Sitarweb.dbo.FN_SRD_RetornaIndFase(PB.NumServico, Pr.idtPedidoRadcom) as 'Fase',
       Sitarweb.dbo.FN_SRD_RetornaSiglaSituacao(h.IdtHabilitacao, Es.IdtEstacao) as 'Situação',
       es.NumEstacao as 'Numero da Estação',
	   e.NumCnpjCpf as 'CNPJ',
	   e.NomeEntidade as 'Entidade',
	   m.NomeMunicipio as 'Município',
	   pb.SiglaUF as 'UF'	 
from ENTIDADE e
inner join HABILITACAO h on h.IdtEntidade = e.IdtEntidade
inner join SRD_PEDIDORADCOM pr on pr.IdtHabilitacao = h.IdtHabilitacao
inner join SRD_PLANOBASICO pb on pb.IdtPlanoBasico = pr.IdtPlanoBasico
inner join estacao es on es.IdtHabilitacao = h.IdtHabilitacao
inner join FREQUENCIA f on f.IdtEstacao = es.IdtEstacao
inner join UnidadeFrequencia uf on uf.IdtUnidadeFrequencia = f.IdtUnidadeFrequencia
inner join Municipio m on m.CodMunicipio = pb.CodMunicipio
where h.NumServico = '231'