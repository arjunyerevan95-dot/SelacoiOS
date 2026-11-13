"""Extract the exact runtime backend Metal source for offline SDK compilation."""
from pathlib import Path
import ast,re,sys
source=Path('overlays/gzselaco-ios/i_metalfx_backend.mm').read_text()
start=source.index('NSString* source=@')
end=source.index('NSError* error=nil;',start)
kernels=''.join(ast.literal_eval(x) for x in re.findall(r'"(?:\\.|[^"\\])*"',source[start:end]))
for name in ('crop','cropDM','influence'):
    assert 'kernel void '+name+'(' in kernels,name
Path(sys.argv[1]).write_text(kernels)
