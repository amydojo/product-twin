import {packagingSpecSchema} from "@product-twin/packaging-schema";import {NextResponse} from "next/server";
export async function POST(request:Request){const body=await request.json().catch(()=>null);const result=packagingSpecSchema.safeParse(body);return NextResponse.json(result.success?{valid:true,spec:result.data}:{valid:false,issues:result.error.issues},{status:result.success?200:422})}
