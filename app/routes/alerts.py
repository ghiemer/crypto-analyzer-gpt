from fastapi import APIRouter, Body
from ..core.alerts import add_alert, delete_alert, list_alerts
from ..core.errors import BAD_ARGUMENT

router = APIRouter(prefix="/alerts", tags=["alerts"])

@router.post("")
async def create(alerts: list[dict] = Body(..., example=[
    {"symbol": "BTCUSDT", "expr": "df.rsi14.iloc[-1] < 30"}])):
    for a in alerts:
        if "symbol" not in a or "expr" not in a:
            raise BAD_ARGUMENT("symbol and expr required")
        await add_alert("default", a["symbol"], a["expr"])
    return {"status": "ok", "count": len(alerts)}

@router.get("")
async def read():
    import traceback
    import sys
    print(f"🔍 DEBUG: /alerts GET endpoint called")
    print(f"🔍 DEBUG: About to import list_alerts from ..core.alerts")
    
    try:
        # Re-import to make sure we have the latest version
        from ..core.alerts import list_alerts as current_list_alerts
        print(f"🔍 DEBUG: Successfully imported list_alerts: {current_list_alerts}")
        print(f"🔍 DEBUG: list_alerts function location: {current_list_alerts.__module__}")
        print(f"🔍 DEBUG: list_alerts function code: {current_list_alerts.__code__.co_filename}:{current_list_alerts.__code__.co_firstlineno}")
        
        print(f"🔍 DEBUG: About to call list_alerts('default')")
        result = await current_list_alerts("default")
        print(f"🔍 DEBUG: list_alerts returned successfully: {result}")
        return result
        
    except Exception as e:
        print(f"❌ ROUTE ERROR: {e}")
        print(f"❌ ROUTE ERROR type: {type(e)}")
        print(f"❌ ROUTE FULL TRACEBACK:")
        traceback.print_exc()
        
        # Additional debugging: check what's actually imported
        import inspect
        print(f"🔍 DEBUG: Checking all imported alert functions...")
        
        try:
            from ..core import alerts as alerts_module
            print(f"🔍 DEBUG: alerts module: {alerts_module}")
            print(f"🔍 DEBUG: alerts module file: {alerts_module.__file__}")
            print(f"🔍 DEBUG: alerts module functions: {[f for f in dir(alerts_module) if callable(getattr(alerts_module, f)) and not f.startswith('_')]}")
            
            # Check if there are multiple list_alerts functions
            list_alerts_func = getattr(alerts_module, 'list_alerts', None)
            if list_alerts_func:
                print(f"🔍 DEBUG: Found list_alerts in module: {list_alerts_func}")
                source = inspect.getsource(list_alerts_func)
                print(f"🔍 DEBUG: list_alerts source code (first 500 chars):")
                print(source[:500])
            else:
                print(f"❌ ERROR: No list_alerts function found in alerts module!")
                
        except Exception as import_error:
            print(f"❌ IMPORT ERROR: {import_error}")
            traceback.print_exc()
        
        raise e

@router.delete("/{symbol}")
async def delete(symbol: str):
    await delete_alert("default", symbol)
    return {"status": "deleted", "symbol": symbol}