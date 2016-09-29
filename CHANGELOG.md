# l10n_cl_dte CHANGELOG.md

[TOC]

### Resúmen
A partir de la versión 8.1.0.0 empezamos a realizar una memoria descriptiva de los cambios de este addon:

Esta versión es totalmente compatible con el proyecto ** LibreDTE **, con ** eFacturaDelSur ** y con ** Facturacion.cl **, este último mediante laa descarga del XML al componente ++DTEPlano++, pero no con los webservices de este último proveedor.

###### _Referencia en el documento_
Incorpora pestaña de referencias.
###### _Detección de nota de pedido de orígen_
si detecta que la factura proviene de una nota de pedido, automáticamente la agrega como referencia. 
###### _Validaciones sobre tipo de documento_
hay una serie de validaciones, respecto a que no se puedan emitir documentos afectos con productos no afectos y ese tipo de cosas.
###### _Nuevas Dependencias_
Requiere la versión  8.1.0.0 del addon l10n_cl_invoice, el cual incorpora un checkbox para determinar si un producto es afecto o no a IVA. Esto se hace para simplificar el cálculo de impuestos, y permite además validar que no se pueda emitir una factura afecta con items no afectos o viceversa.
###### _Impresión de cedible_
Para la opción de uso de ++LibreDTE++, se incorpora la posibilidad de imprimir la copia cedible en el PDF. Lo que mencionaste no se me ha reproducido ninguno de esos errores, sin embargo para el PDF ahora se controla que el PDF se descargue una sola vez. Antes si presionabas 10 veces el botón traer pdf traía 10 pdfs iguales, ahora revisa si ya está el pdf para no traerlo de nuevo y se incorporó una opción de imprimir la cedible.[^]
###### _TO-DOs_
Quedan por hacer algunas validaciones extras: por ejemplo, no tiene un control respecto a que si al producto no afecto se le incorpora IVA, no emite validación en ese sentido. Para esta finalidad, se ha incluído una función que está en desarrollo, la cual se denomina "_pr_prices", en donde se prevee realizar los cálculos de impuestos), la cual se habilitará en próximas versiones.


[^]: Thanks: Juan Plaza - ISOS
